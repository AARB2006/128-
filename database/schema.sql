/*
Supabase database setup: tables, indexes and row-level security
for profiles, songs, playlists, imports and exports.
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

-- songs and import tables are written only by the backend (service role),
-- which enforces the import quota; users can read, and delete their songs
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
-- Written only by the backend (secret key); users can read their own.
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
