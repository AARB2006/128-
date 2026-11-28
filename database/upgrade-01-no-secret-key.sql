-- ---------------------------------------------------------------
-- 10. Backend without the secret key
-- ---------------------------------------------------------------
-- The backend runs on each family computer, so it must not hold the secret
-- key (which bypasses row-level security for EVERY user). Instead:
--
-- * Starting an import or export is a function called with the user's own
--   login token. The function checks the rules (one job at a time, daily
--   limits, playlist ownership) and records the job for auth.uid() only.
-- * It returns a random job key. Progress updates from the background work
--   send that key instead of a login token (which may expire during a long
--   export). A key can only update its own job, and stops working when the
--   job finishes. Only its SHA-256 hash is stored.
-- * Users can delete their own finished exports directly (row-level security).
--
-- Errors use SQLSTATE 'PTxxx', which PostgREST turns into HTTP status xxx,
-- so the backend can pass the message straight to the app.
--
-- Safe to run more than once. The old backend (with the secret key) keeps
-- working after this runs, so it can be applied before the new backend.
-- ---------------------------------------------------------------

-- Limits, the same for every user. Change one with, for example:
--   update private.app_limits set value = 200 where name = 'daily_import_links';
create table if not exists private.app_limits (
    name  text primary key,
    value integer not null check (value >= 0)
);
insert into private.app_limits (name, value) values
    ('daily_import_links', 100),   -- links per user per 24 hours
    ('max_export_songs',   100),   -- songs in one export
    ('daily_export_songs', 300)    -- songs exported per user per 24 hours
on conflict (name) do nothing;

-- Keys for running jobs (hashes only). Not reachable through the API.
create table if not exists private.job_keys (
    job_id     uuid primary key,
    kind       text not null check (kind in ('import', 'export')),
    key_hash   bytea not null,
    created_at timestamptz not null default now()
);

revoke all on private.app_limits, private.job_keys from public, anon, authenticated;


-- ---- private helpers ------------------------------------------------------------

create or replace function private.limit_value(p_name text)
returns integer
language sql
stable
set search_path = ''
as $$
    select value from private.app_limits where name = p_name
$$;

-- A new random key (244 random bits) for a job; only its hash is kept.
create or replace function private.new_job_key(p_kind text, p_job_id uuid)
returns text
language plpgsql
set search_path = ''
as $$
declare
    v_key text := replace(gen_random_uuid()::text || gen_random_uuid()::text, '-', '');
begin
    insert into private.job_keys (job_id, kind, key_hash)
    values (p_job_id, p_kind, sha256(convert_to(v_key, 'UTF8')));
    return v_key;
end;
$$;

create or replace function private.check_job_key(p_kind text, p_job_id uuid, p_key text)
returns void
language plpgsql
stable
set search_path = ''
as $$
begin
    if p_key is null or not exists (
        select 1 from private.job_keys k
        where k.job_id = p_job_id
          and k.kind = p_kind
          and k.key_hash = sha256(convert_to(p_key, 'UTF8'))
    ) then
        raise sqlstate 'PT403' using message = 'This job can no longer be updated.';
    end if;
end;
$$;

-- Marks a job as interrupted (if it is still running) and forgets its key.
create or replace function private.interrupt_job(p_kind text, p_job_id uuid)
returns void
language plpgsql
set search_path = ''
as $$
begin
    if p_kind = 'import' then
        update public.import_items
           set status = 'failed',
               error_message = 'The import was interrupted. Please try again.',
               processed_at = now()
         where batch_id = p_job_id and status = 'pending';
        update public.import_batches
           set status = 'failed', completed_at = now()
         where batch_id = p_job_id and status in ('pending', 'processing');
    else
        update public.export_items
           set status = 'skipped',
               error_message = 'The export was interrupted. Please try again.',
               processed_at = now()
         where export_id = p_job_id and status = 'pending';
        update public.exports
           set status = 'failed',
               error_message = 'The export was interrupted. Please try again.',
               completed_at = now()
         where export_id = p_job_id and status in ('pending', 'processing', 'packaging');
    end if;
    delete from private.job_keys where job_id = p_job_id;
end;
$$;

-- Jobs still "running" long after they could possibly be (the computer
-- crashed, or its backend never came back): mark them interrupted so they
-- don't block new ones. Imports take seconds; an export of the maximum
-- size takes well under six hours.
create or replace function private.fail_stale_jobs(p_owner uuid)
returns void
language plpgsql
set search_path = ''
as $$
declare
    v_id uuid;
begin
    for v_id in
        select batch_id from public.import_batches
         where owner_id = p_owner
           and status in ('pending', 'processing')
           and created_at < now() - interval '1 hour'
    loop
        perform private.interrupt_job('import', v_id);
    end loop;

    for v_id in
        select export_id from public.exports
         where owner_id = p_owner
           and status in ('pending', 'processing', 'packaging')
           and created_at < now() - interval '6 hours'
    loop
        perform private.interrupt_job('export', v_id);
    end loop;
end;
$$;

revoke execute on function
    private.limit_value(text),
    private.new_job_key(text, uuid),
    private.check_job_key(text, uuid, text),
    private.interrupt_job(text, uuid),
    private.fail_stale_jobs(uuid)
from public, anon, authenticated;


-- ---- imports ------------------------------------------------------------------------

-- Called with the user's login token. p_items: the links in order, as
-- [{line_no, submitted_url, video_id, status, error_message}], where status
-- is 'pending' (to look up), 'invalid' or 'duplicate' (decided by the backend).
-- Links already in the user's library become 'duplicate' here.
-- Returns {batch_id, job_key (null if nothing to look up), status, items}.
create or replace function public.start_import(p_items jsonb)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_owner  uuid := auth.uid();
    v_count  integer;
    v_limit  integer;
    v_used   integer;
    v_batch  uuid;
    v_key    text;
    v_work   boolean;
    v_status text;
    v_plan   jsonb;
begin
    if v_owner is null then
        raise sqlstate 'PT401' using message = 'You must be signed in to do this.';
    end if;
    if p_items is null or jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 then
        raise sqlstate 'PT422' using message = 'Enter at least one YouTube link.';
    end if;

    v_count := jsonb_array_length(p_items);
    if v_count > 10 then
        raise sqlstate 'PT422' using message = 'You can import at most 10 links at a time.';
    end if;

    if exists (
        select 1 from jsonb_array_elements(p_items) with ordinality as e(item, n)
        where jsonb_typeof(item) <> 'object'
           or item ->> 'line_no' is distinct from n::text
           or coalesce(item ->> 'status', '') not in ('pending', 'duplicate', 'invalid')
           or length(coalesce(item ->> 'submitted_url', '')) not between 1 and 2048
           or (item ->> 'video_id' is not null and item ->> 'video_id' !~ '^[A-Za-z0-9_-]{11}$')
           or (item ->> 'status' = 'pending' and item ->> 'video_id' is null)
    ) then
        raise sqlstate 'PT422' using message = 'The import request was not valid.';
    end if;

    -- One start at a time per user, so the checks below can't race.
    perform pg_advisory_xact_lock(hashtextextended('import:' || v_owner::text, 0));
    perform private.fail_stale_jobs(v_owner);

    if exists (select 1 from public.import_batches
               where owner_id = v_owner and status in ('pending', 'processing')) then
        raise sqlstate 'PT409' using message = 'An import is already running. Wait for it to finish.';
    end if;

    v_limit := private.limit_value('daily_import_links');
    select coalesce(sum(total_links), 0) into v_used
      from public.import_batches
     where owner_id = v_owner and created_at >= now() - interval '24 hours';
    if v_used + v_count > v_limit then
        raise sqlstate 'PT429' using message = format(
            'Daily import limit reached. You can import %s more link(s) in the next 24 hours.',
            greatest(v_limit - v_used, 0));
    end if;

    -- Decide each link's starting status (library duplicates included).
    select jsonb_agg(jsonb_build_object(
               'line_no', n,
               'submitted_url', item ->> 'submitted_url',
               'video_id', item ->> 'video_id',
               'status', case when owned then 'duplicate' else item ->> 'status' end,
               'error_message', case when owned then 'Already in your library.'
                                     else left(item ->> 'error_message', 500) end)
           order by n)
      into v_plan
      from (
        select e.item, e.n,
               (e.item ->> 'status' = 'pending' and exists (
                   select 1 from public.songs s
                    where s.owner_id = v_owner and s.video_id = e.item ->> 'video_id')) as owned
          from jsonb_array_elements(p_items) with ordinality as e(item, n)
      ) planned;

    v_work := exists (select 1 from jsonb_array_elements(v_plan) as x(item)
                      where item ->> 'status' = 'pending');
    v_status := case
        when v_work then 'processing'
        when exists (select 1 from jsonb_array_elements(v_plan) as x(item)
                     where item ->> 'status' = 'invalid') then 'failed'
        else 'completed'
    end;

    insert into public.import_batches (owner_id, total_links, status, completed_at)
    values (v_owner, v_count, v_status, case when v_work then null else now() end)
    returning batch_id into v_batch;

    insert into public.import_items
        (batch_id, line_no, submitted_url, video_id, status, error_message, processed_at)
    select v_batch, line_no, submitted_url, video_id, status, error_message,
           case when status = 'pending' then null else now() end
      from jsonb_to_recordset(v_plan) as plan(
               line_no smallint, submitted_url text, video_id text,
               status text, error_message text);

    if v_work then
        v_key := private.new_job_key('import', v_batch);
    end if;

    return jsonb_build_object(
        'batch_id', v_batch,
        'job_key', v_key,
        'status', v_status,
        'items', (select jsonb_agg(jsonb_build_object(
                          'line_no', item -> 'line_no', 'status', item -> 'status',
                          'error_message', item -> 'error_message'))
                    from jsonb_array_elements(v_plan) as x(item)));
end;
$$;

-- Called with the job key. Saves one looked-up link: p_status 'success'
-- (with the title and duration) adds the song, or 'failed' (with a message).
-- Returns the link's final status ('duplicate' if the song was added in the
-- meantime).
create or replace function public.record_import_item(
    p_batch_id uuid,
    p_job_key text,
    p_line_no integer,
    p_status text,
    p_error_message text default null,
    p_title text default null,
    p_duration_seconds integer default null
)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_owner uuid;
    v_video text;
    v_item  text;
    v_song  uuid;
    v_final text;
    v_error text;
begin
    perform private.check_job_key('import', p_batch_id, p_job_key);

    select owner_id into v_owner from public.import_batches
     where batch_id = p_batch_id and status in ('pending', 'processing')
     for update;
    if not found then
        raise sqlstate 'PT409' using message = 'This import is no longer running.';
    end if;

    select video_id, status into v_video, v_item from public.import_items
     where batch_id = p_batch_id and line_no = p_line_no
     for update;
    if not found or v_item <> 'pending' then
        raise sqlstate 'PT409' using message = 'This link was already processed.';
    end if;

    if p_status = 'success' then
        if p_title is null or length(btrim(p_title)) = 0 then
            raise sqlstate 'PT422' using message = 'A song needs a title.';
        end if;
        insert into public.songs
            (owner_id, video_id, source_url, title, duration_seconds, metadata_fetched_at)
        values (v_owner, v_video, 'https://www.youtube.com/watch?v=' || v_video,
                left(p_title, 1000), p_duration_seconds, now())
        on conflict (owner_id, video_id) do nothing
        returning song_id into v_song;

        if v_song is null then
            v_final := 'duplicate';
            v_error := 'Already in your library.';
        else
            v_final := 'success';
        end if;
    elsif p_status = 'failed' then
        v_final := 'failed';
        v_error := left(coalesce(p_error_message, 'This video could not be imported.'), 500);
    else
        raise sqlstate 'PT422' using message = 'A link can only succeed or fail.';
    end if;

    update public.import_items
       set status = v_final, error_message = v_error, song_id = v_song, processed_at = now()
     where batch_id = p_batch_id and line_no = p_line_no;

    return v_final;
end;
$$;

-- Called with the job key when the background work ends (normally or not).
-- Links still pending are marked failed. Returns the batch's final status.
create or replace function public.finish_import(p_batch_id uuid, p_job_key text)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_added    boolean;
    v_problems boolean;
    v_status   text;
begin
    perform private.check_job_key('import', p_batch_id, p_job_key);

    update public.import_items
       set status = 'failed',
           error_message = 'The import stopped unexpectedly.',
           processed_at = now()
     where batch_id = p_batch_id and status = 'pending';

    v_added := exists (select 1 from public.import_items
                       where batch_id = p_batch_id and status = 'success');
    v_problems := exists (select 1 from public.import_items
                          where batch_id = p_batch_id and status in ('failed', 'invalid'));
    v_status := case
        when v_problems and v_added then 'partial'
        when v_problems then 'failed'
        else 'completed'
    end;

    update public.import_batches
       set status = v_status, completed_at = now()
     where batch_id = p_batch_id and status in ('pending', 'processing');

    delete from private.job_keys where job_id = p_batch_id;
    return v_status;
end;
$$;


-- ---- exports ------------------------------------------------------------------------

-- Called with the user's login token. Records the export of one of the user's
-- playlists and returns {export_id, job_key, playlist_name, tracks}, where
-- tracks = [{position, song_id, video_id, title}] in playlist order.
create or replace function public.start_export(p_playlist_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_owner  uuid := auth.uid();
    v_name   text;
    v_count  integer;
    v_max    integer;
    v_limit  integer;
    v_used   integer;
    v_export uuid;
    v_key    text;
begin
    if v_owner is null then
        raise sqlstate 'PT401' using message = 'You must be signed in to do this.';
    end if;

    select name into v_name from public.playlists
     where playlist_id = p_playlist_id and owner_id = v_owner;
    if not found then
        raise sqlstate 'PT404' using message = 'Playlist not found.';
    end if;

    select count(*) into v_count
      from public.playlist_songs ps
      join public.songs s on s.song_id = ps.song_id and s.owner_id = v_owner
     where ps.playlist_id = p_playlist_id;
    if v_count = 0 then
        raise sqlstate 'PT409' using message = 'This playlist has no songs to export.';
    end if;

    v_max := private.limit_value('max_export_songs');
    if v_count > v_max then
        raise sqlstate 'PT422' using message = format(
            'Playlists with more than %s songs can''t be exported yet.', v_max);
    end if;

    perform pg_advisory_xact_lock(hashtextextended('export:' || v_owner::text, 0));
    perform private.fail_stale_jobs(v_owner);

    v_limit := private.limit_value('daily_export_songs');
    select coalesce(sum(total_songs), 0) into v_used
      from public.exports
     where owner_id = v_owner
       and created_at >= now() - interval '24 hours'
       and not (status in ('failed', 'cancelled') and exported_songs = 0);
    if v_used + v_count > v_limit then
        raise sqlstate 'PT429' using message = format(
            'Daily export limit reached. You can export %s more song(s) in the next 24 hours.',
            greatest(v_limit - v_used, 0));
    end if;

    begin
        insert into public.exports (owner_id, playlist_id, total_songs, status)
        values (v_owner, p_playlist_id, v_count, 'pending')
        returning export_id into v_export;
    exception when unique_violation then
        raise sqlstate 'PT409' using message = 'An export is already running. Wait for it to finish.';
    end;

    insert into public.export_items (export_id, position, song_id)
    select v_export, ps.position, ps.song_id
      from public.playlist_songs ps
      join public.songs s on s.song_id = ps.song_id and s.owner_id = v_owner
     where ps.playlist_id = p_playlist_id;

    v_key := private.new_job_key('export', v_export);

    return jsonb_build_object(
        'export_id', v_export,
        'job_key', v_key,
        'playlist_name', v_name,
        'tracks', (select jsonb_agg(jsonb_build_object(
                           'position', ps.position, 'song_id', s.song_id,
                           'video_id', s.video_id, 'title', s.title)
                           order by ps.position)
                     from public.playlist_songs ps
                     join public.songs s on s.song_id = ps.song_id and s.owner_id = v_owner
                    where ps.playlist_id = p_playlist_id));
end;
$$;

-- Called with the job key. p_fields may contain: status, percent,
-- exported_songs, error_message, file_size_bytes, file_expires_at, and
-- started_at / completed_at (the database's clock is used for those two).
-- A finishing status (completed, partial, failed, cancelled) retires the key.
create or replace function public.update_export_job(
    p_export_id uuid,
    p_job_key text,
    p_fields jsonb
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_status text;
begin
    perform private.check_job_key('export', p_export_id, p_job_key);

    if p_fields is null or jsonb_typeof(p_fields) <> 'object' or exists (
        select 1 from jsonb_object_keys(p_fields) as k
        where k not in ('status', 'percent', 'exported_songs', 'error_message',
                        'file_size_bytes', 'file_expires_at', 'started_at', 'completed_at')
    ) or coalesce(p_fields ->> 'status', 'processing') not in
         ('processing', 'packaging', 'completed', 'partial', 'failed', 'cancelled') then
        raise sqlstate 'PT422' using message = 'The export update was not valid.';
    end if;

    perform 1 from public.exports
     where export_id = p_export_id and status in ('pending', 'processing', 'packaging')
     for update;
    if not found then
        raise sqlstate 'PT409' using message = 'This export is no longer running.';
    end if;

    update public.exports set
        status          = coalesce(p_fields ->> 'status', status),
        percent         = case when p_fields ? 'percent'
                               then (p_fields ->> 'percent')::smallint else percent end,
        exported_songs  = case when p_fields ? 'exported_songs'
                               then (p_fields ->> 'exported_songs')::integer else exported_songs end,
        error_message   = case when p_fields ? 'error_message'
                               then left(p_fields ->> 'error_message', 500) else error_message end,
        file_size_bytes = case when p_fields ? 'file_size_bytes'
                               then (p_fields ->> 'file_size_bytes')::bigint else file_size_bytes end,
        file_expires_at = case when p_fields ? 'file_expires_at'
                               then (p_fields ->> 'file_expires_at')::timestamptz else file_expires_at end,
        started_at      = case when p_fields ? 'started_at' then now() else started_at end,
        completed_at    = case when p_fields ? 'completed_at' then now() else completed_at end
    where export_id = p_export_id
    returning status into v_status;

    if v_status in ('completed', 'partial', 'failed', 'cancelled') then
        delete from private.job_keys where job_id = p_export_id;
    end if;
end;
$$;

-- Called with the job key: one song's result.
create or replace function public.update_export_item_job(
    p_export_id uuid,
    p_job_key text,
    p_position integer,
    p_status text,
    p_error_message text default null
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
    perform private.check_job_key('export', p_export_id, p_job_key);
    if p_status not in ('success', 'failed', 'skipped') then
        raise sqlstate 'PT422' using message = 'A song can only succeed, fail or be skipped.';
    end if;

    update public.export_items
       set status = p_status, error_message = left(p_error_message, 500), processed_at = now()
     where export_id = p_export_id and position = p_position;
end;
$$;

-- Called with the job key: every song not processed yet is skipped.
create or replace function public.skip_pending_export_items_job(
    p_export_id uuid,
    p_job_key text,
    p_reason text
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
    perform private.check_job_key('export', p_export_id, p_job_key);

    update public.export_items
       set status = 'skipped', error_message = left(p_reason, 500), processed_at = now()
     where export_id = p_export_id and status = 'pending';
end;
$$;


-- ---- jobs left over from a previous run -----------------------------------------------

-- Called with the job key when the backend starts again on the same computer
-- and finds a job it was running when it stopped.
create or replace function public.interrupt_job(p_kind text, p_job_id uuid, p_job_key text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
    perform private.check_job_key(p_kind, p_job_id, p_job_key);
    perform private.interrupt_job(p_kind, p_job_id);
end;
$$;


-- ---- who may call what ----------------------------------------------------------------

revoke all on function
    public.start_import(jsonb),
    public.record_import_item(uuid, text, integer, text, text, text, integer),
    public.finish_import(uuid, text),
    public.start_export(uuid),
    public.update_export_job(uuid, text, jsonb),
    public.update_export_item_job(uuid, text, integer, text, text),
    public.skip_pending_export_items_job(uuid, text, text),
    public.interrupt_job(text, uuid, text)
from public, anon, authenticated;

-- Starting a job needs a signed-in user.
grant execute on function
    public.start_import(jsonb),
    public.start_export(uuid)
to authenticated;

-- Job-key functions: the key is the permission, so a login token isn't
-- needed (it may have expired while a long export ran).
grant execute on function
    public.record_import_item(uuid, text, integer, text, text, text, integer),
    public.finish_import(uuid, text),
    public.update_export_job(uuid, text, jsonb),
    public.update_export_item_job(uuid, text, integer, text, text),
    public.skip_pending_export_items_job(uuid, text, text),
    public.interrupt_job(text, uuid, text)
to anon, authenticated;

-- Users may delete their own finished exports (Export History).
grant delete on public.exports to authenticated;
drop policy if exists exports_delete on public.exports;
create policy exports_delete on public.exports
    for delete to authenticated
    using (owner_id = (select auth.uid())
           and status not in ('pending', 'processing', 'packaging'));
