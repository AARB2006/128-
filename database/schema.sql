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
grant  update (name) on public.playlists to authenticated;

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