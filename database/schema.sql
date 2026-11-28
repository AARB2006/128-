/*
Supabase database setup: tables, indexes, row-level security, Realtime and
the functions the backend uses (it holds no secret key) for profiles, songs,
playlists, imports and exports.
*/

-- ---------------------------------------------------------------
-- 1. Tables
-- ---------------------------------------------------------------
create table public.profiles (
    id           uuid primary key references auth.users (id) on delete cascade,
    display_name text,
    email        text not null unique,
    created_at   timestamptz not null default now()
);

create table public.songs (
    song_id             uuid primary key default gen_random_uuid(),
    owner_id            uuid not null references public.profiles (id) on delete cascade,
    video_id            text not null,
    source_url          text not null,
    title               text not null,
    duration_seconds    integer check (duration_seconds is null or duration_seconds >= 0),
    date_added          timestamptz not null default now(),
    metadata_fetched_at timestamptz,
    constraint songs_owner_video_unique unique (owner_id, video_id)
);
create index songs_owner_idx on public.songs (owner_id);

create table public.playlists (
    playlist_id uuid primary key default gen_random_uuid(),
    owner_id    uuid not null references public.profiles (id) on delete cascade,
    name        text not null check (length(btrim(name)) > 0),
        description text check (description is null or length(description) <= 500),
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);
create index playlists_owner_idx on public.playlists (owner_id);

create table public.playlist_songs (
    playlist_song_id uuid primary key default gen_random_uuid(),
    playlist_id      uuid not null references public.playlists (playlist_id) on delete cascade,
    song_id          uuid not null references public.songs (song_id) on delete cascade,
    position         integer not null check (position >= 1),
    added_at         timestamptz not null default now(),
    constraint playlist_songs_song_unique unique (playlist_id, song_id),
    -- deferred so a reorder can swap positions within one transaction
    constraint playlist_songs_position_unique unique (playlist_id, position)
        deferrable initially deferred
);
create index playlist_songs_song_idx on public.playlist_songs (song_id);

create table public.import_batches (
    batch_id     uuid primary key default gen_random_uuid(),
    owner_id     uuid not null references public.profiles (id) on delete cascade,
    total_links  smallint not null check (total_links between 1 and 10),
    status       text not null default 'pending'
                 check (status in ('pending', 'processing', 'completed', 'partial', 'failed')),
    created_at   timestamptz not null default now(),
    completed_at timestamptz
);
create index import_batches_owner_idx on public.import_batches (owner_id);

create table public.import_items (
    item_id       uuid primary key default gen_random_uuid(),
    batch_id      uuid not null references public.import_batches (batch_id) on delete cascade,
    line_no       smallint not null check (line_no between 1 and 10),
    submitted_url text not null,
    video_id      text,
    song_id       uuid references public.songs (song_id) on delete set null,
    status        text not null default 'pending'
                  check (status in ('pending', 'success', 'duplicate', 'invalid', 'failed')),
    error_message text,
    processed_at  timestamptz,
    constraint import_items_batch_line_unique unique (batch_id, line_no)
);
create index import_items_song_idx on public.import_items (song_id);

-- ---------------------------------------------------------------
-- 2. Private schema for trigger functions (not exposed via the API)
-- ---------------------------------------------------------------
create schema private;
revoke all on schema private from public, anon;
grant usage on schema private to authenticated;

-- ---------------------------------------------------------------
-- 3. Triggers
-- ---------------------------------------------------------------

-- create a profile on first Google sign-in (idempotent)
create function private.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    insert into public.profiles (id, display_name, email)
    values (
        new.id,
        coalesce(new.raw_user_meta_data ->> 'full_name',
                 new.raw_user_meta_data ->> 'name',
                 split_part(new.email, '@', 1)),
        new.email
    )
    on conflict (id) do nothing;
    return new;
end;
$$;

create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function private.handle_new_user();

-- keep profiles.email in sync with auth
create function private.sync_user_email()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    update public.profiles set email = new.email where id = new.id;
    return new;
end;
$$;

create trigger on_auth_user_email_changed
    after update of email on auth.users
    for each row
    when (old.email is distinct from new.email)
    execute function private.sync_user_email();

-- updated_at when the playlist itself is renamed
create function private.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger playlists_set_updated_at
    before update on public.playlists
    for each row execute function private.set_updated_at();

-- updated_at when songs are added, removed or reordered
-- (security definer: users only hold column-level UPDATE on playlists.name)
create function private.touch_playlist()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    update public.playlists
    set updated_at = now()
    where playlist_id = coalesce(new.playlist_id, old.playlist_id);
    return null;
end;
$$;

create trigger playlist_songs_touch_playlist
    after insert or update or delete on public.playlist_songs
    for each row execute function private.touch_playlist();

revoke execute on all functions in schema private from public, anon, authenticated;

-- ---------------------------------------------------------------
-- 4. Row Level Security: enable
-- ---------------------------------------------------------------
alter table public.profiles       enable row level security;
alter table public.songs          enable row level security;
alter table public.playlists      enable row level security;
alter table public.playlist_songs enable row level security;
alter table public.import_batches enable row level security;
alter table public.import_items   enable row level security;

-- ---------------------------------------------------------------
-- 5. Table privileges (column-level limits back up the policies)
-- ---------------------------------------------------------------
revoke all on all tables in schema public from anon;

revoke insert, update, delete on public.profiles from authenticated;
grant  update (display_name)   on public.profiles to authenticated;

-- songs and import tables are written only through the import functions in
-- section 10, which enforce the import rules; users can read, and delete
-- their songs
revoke insert, update         on public.songs          from authenticated;
revoke insert, update, delete on public.import_batches from authenticated;
revoke insert, update, delete on public.import_items   from authenticated;

revoke update on public.playlists from authenticated;
grant  update (name, description) on public.playlists to authenticated;

revoke update on public.playlist_songs from authenticated;
grant  update (position) on public.playlist_songs to authenticated;

-- ---------------------------------------------------------------
-- 6. Row Level Security: policies
-- ---------------------------------------------------------------

-- profiles
create policy profiles_select on public.profiles
    for select to authenticated
    using (id = (select auth.uid()));

create policy profiles_update on public.profiles
    for update to authenticated
    using (id = (select auth.uid()))
    with check (id = (select auth.uid()));

-- songs
create policy songs_select on public.songs
    for select to authenticated
    using (owner_id = (select auth.uid()));

create policy songs_delete on public.songs
    for delete to authenticated
    using (owner_id = (select auth.uid()));

-- playlists
create policy playlists_select on public.playlists
    for select to authenticated
    using (owner_id = (select auth.uid()));

create policy playlists_insert on public.playlists
    for insert to authenticated
    with check (owner_id = (select auth.uid()));

create policy playlists_update on public.playlists
    for update to authenticated
    using (owner_id = (select auth.uid()))
    with check (owner_id = (select auth.uid()));

create policy playlists_delete on public.playlists
    for delete to authenticated
    using (owner_id = (select auth.uid()));

-- playlist_songs: the playlist must be yours, and so must the song
create policy playlist_songs_select on public.playlist_songs
    for select to authenticated
    using (exists (
        select 1 from public.playlists p
        where p.playlist_id = playlist_songs.playlist_id
          and p.owner_id = (select auth.uid())));

create policy playlist_songs_insert on public.playlist_songs
    for insert to authenticated
    with check (
        exists (select 1 from public.playlists p
                where p.playlist_id = playlist_songs.playlist_id
                  and p.owner_id = (select auth.uid()))
        and exists (select 1 from public.songs s
                    where s.song_id = playlist_songs.song_id
                      and s.owner_id = (select auth.uid())));

create policy playlist_songs_update on public.playlist_songs
    for update to authenticated
    using (exists (
        select 1 from public.playlists p
        where p.playlist_id = playlist_songs.playlist_id
          and p.owner_id = (select auth.uid())))
    with check (exists (
        select 1 from public.playlists p
        where p.playlist_id = playlist_songs.playlist_id
          and p.owner_id = (select auth.uid())));

create policy playlist_songs_delete on public.playlist_songs
    for delete to authenticated
    using (exists (
        select 1 from public.playlists p
        where p.playlist_id = playlist_songs.playlist_id
          and p.owner_id = (select auth.uid())));

-- import tables: read-only for the owner
create policy import_batches_select on public.import_batches
    for select to authenticated
    using (owner_id = (select auth.uid()));

create policy import_items_select on public.import_items
    for select to authenticated
    using (exists (
        select 1 from public.import_batches b
        where b.batch_id = import_items.batch_id
          and b.owner_id = (select auth.uid())));

-- ---------------------------------------------------------------
-- Exports: one row per export job. Also the Export History list.
-- Stores references only: names and titles are read from
-- playlists and songs when the history is shown.
-- Written only through the export functions in section 10; users can read
-- their own, and delete their own finished exports.
-- ---------------------------------------------------------------
create table public.exports (
    export_id       uuid primary key default gen_random_uuid(),
    owner_id        uuid not null references public.profiles (id) on delete cascade,
    playlist_id     uuid references public.playlists (playlist_id) on delete set null,
    format          text not null default 'zip' check (format in ('zip')),
    total_songs     integer not null check (total_songs between 1 and 1000),
    exported_songs  integer not null default 0 check (exported_songs >= 0),
    percent         smallint not null default 0 check (percent between 0 and 100),
    status          text not null default 'pending'
                    check (status in ('pending', 'processing', 'packaging',
                                      'completed', 'partial', 'failed', 'cancelled')),
    error_message   text,
    file_size_bytes bigint,
    created_at      timestamptz not null default now(),
    started_at      timestamptz,
    completed_at    timestamptz,
    file_expires_at timestamptz
);
create index exports_owner_created_idx on public.exports (owner_id, created_at desc);
create index exports_playlist_idx on public.exports (playlist_id);

-- At most one running export per user, enforced by the database.
create unique index exports_one_active_per_owner
    on public.exports (owner_id)
    where status in ('pending', 'processing', 'packaging');

-- Which song was at which position, and whether it made it into the ZIP.
create table public.export_items (
    export_id     uuid not null references public.exports (export_id) on delete cascade,
    position      integer not null check (position >= 1),
    song_id       uuid references public.songs (song_id) on delete set null,
    status        text not null default 'pending'
                  check (status in ('pending', 'success', 'failed', 'skipped')),
    error_message text,
    processed_at  timestamptz,
    primary key (export_id, position)
);
create index export_items_song_idx on public.export_items (song_id);

alter table public.exports      enable row level security;
alter table public.export_items enable row level security;

revoke all on public.exports, public.export_items from anon;
revoke insert, update, delete on public.exports      from authenticated;
revoke insert, update, delete on public.export_items from authenticated;

create policy exports_select on public.exports
    for select to authenticated
    using (owner_id = (select auth.uid()));

create policy export_items_select on public.export_items
    for select to authenticated
    using (exists (
        select 1 from public.exports e
        where e.export_id = export_items.export_id
          and e.owner_id = (select auth.uid())));


-- ---------------------------------------------------------------
-- 8. Playlist functions (called by the browser with supabase.rpc)
--    They run as the signed-in user, so row-level security still
--    applies. Each one is a single transaction.
-- ---------------------------------------------------------------

-- Appends songs to the end of a playlist, skipping ones already in it.
-- Returns how many were added.
create or replace function public.add_songs_to_playlist(
    p_playlist_id uuid,
    p_song_ids    uuid[]
) returns integer
language plpgsql
set search_path = ''
as $$
declare added int;
begin
  perform 1 from public.playlists where playlist_id = p_playlist_id for update;
  if not found then raise exception 'Playlist not found.'; end if;

  insert into public.playlist_songs (playlist_id, song_id, position)
  select p_playlist_id, t.song_id,
         coalesce((select max(position) from public.playlist_songs
                   where playlist_id = p_playlist_id), 0) + row_number() over (order by t.ord)
    from (select song_id, min(ord) as ord
            from unnest(p_song_ids) with ordinality as u(song_id, ord)
           group by song_id) t
   where not exists (select 1 from public.playlist_songs ps
                     where ps.playlist_id = p_playlist_id and ps.song_id = t.song_id);

  get diagnostics added = row_count;
  return added;
end
$$;

-- Takes every song in the playlist in its new order and renumbers them
-- 1 to n. Fails if the list doesn't match what is stored (the playlist
-- was changed elsewhere).
create or replace function public.reorder_playlist_songs(
    p_playlist_id uuid,
    p_song_ids    uuid[]
) returns void
language plpgsql
set search_path = ''
as $$
declare current_count int;
begin
  select count(*) into current_count
    from public.playlist_songs where playlist_id = p_playlist_id;

  if cardinality(p_song_ids) <> current_count
     or (select count(distinct x) from unnest(p_song_ids) as x) <> current_count
     or exists (select 1 from unnest(p_song_ids) as x
                where x not in (select song_id from public.playlist_songs
                                where playlist_id = p_playlist_id))
  then
    raise exception 'This playlist has changed. Reload it and try again.';
  end if;

  update public.playlist_songs ps
     set position = o.new_pos::int
    from unnest(p_song_ids) with ordinality as o(song_id, new_pos)
   where ps.playlist_id = p_playlist_id and ps.song_id = o.song_id;
end
$$;

revoke all on function public.add_songs_to_playlist(uuid, uuid[])    from public, anon;
revoke all on function public.reorder_playlist_songs(uuid, uuid[])   from public, anon;
grant execute on function public.add_songs_to_playlist(uuid, uuid[])  to authenticated;
grant execute on function public.reorder_playlist_songs(uuid, uuid[]) to authenticated;

-- ---------------------------------------------------------------
-- 9. Realtime: open pages hear about changes made elsewhere
-- ---------------------------------------------------------------
-- Row-level security still applies: each user only receives their own new
-- and changed rows. (Deletes carry only the row's id.)
alter publication supabase_realtime add table
    public.songs, public.playlists, public.playlist_songs, public.exports;

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
