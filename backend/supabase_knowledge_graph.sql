create table if not exists public.concept_maps (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  document_id uuid not null,
  title text not null default 'Knowledge map',
  subject text,
  topic text,
  concepts jsonb not null default '[]'::jsonb,
  relationships jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.concept_map_progress (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  map_id uuid not null references public.concept_maps(id) on delete cascade,
  concept_id text not null,
  concept_name text,
  status text not null default 'review',
  score numeric not null default 0,
  notes text,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists idx_concept_maps_user_created
  on public.concept_maps (user_id, created_at desc);

create index if not exists idx_concept_map_progress_user_map
  on public.concept_map_progress (user_id, map_id, concept_id);

create policy if not exists concept_maps_select_own_rows
  on public.concept_maps
  for select
  using (auth.uid() = user_id);

create policy if not exists concept_maps_insert_own_rows
  on public.concept_maps
  for insert
  with check (auth.uid() = user_id);

create policy if not exists concept_maps_update_own_rows
  on public.concept_maps
  for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy if not exists concept_maps_delete_own_rows
  on public.concept_maps
  for delete
  using (auth.uid() = user_id);

create policy if not exists concept_map_progress_select_own_rows
  on public.concept_map_progress
  for select
  using (auth.uid() = user_id);

create policy if not exists concept_map_progress_insert_own_rows
  on public.concept_map_progress
  for insert
  with check (auth.uid() = user_id);

create policy if not exists concept_map_progress_update_own_rows
  on public.concept_map_progress
  for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy if not exists concept_map_progress_delete_own_rows
  on public.concept_map_progress
  for delete
  using (auth.uid() = user_id);
