-- Production readiness migration for the AI Study Assistant.
-- This script is additive only and does not modify existing user data.

create table if not exists public.study_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  started_at timestamptz not null,
  ended_at timestamptz not null,
  duration_minutes integer not null check (duration_minutes between 5 and 720),
  session_type text not null default 'study',
  note text,
  date_local date not null,
  created_at timestamptz not null default now(),
  constraint study_sessions_time_order check (ended_at > started_at),
  constraint study_sessions_unique_session unique (user_id, started_at, ended_at)
);

create index if not exists idx_study_sessions_user_started
  on public.study_sessions (user_id, started_at desc);

create index if not exists idx_study_sessions_date_local
  on public.study_sessions (user_id, date_local);

alter table public.users
  add column if not exists daily_study_goal integer not null default 60 check (daily_study_goal between 15 and 720);

create index if not exists idx_users_email
  on public.users (email);

create index if not exists idx_documents_user_id
  on public.documents (user_id);

create index if not exists idx_documents_user_deleted
  on public.documents (user_id, is_deleted);

create index if not exists idx_streaks_user_id
  on public.streaks (user_id);

create index if not exists idx_notes_user_id
  on public.notes (user_id);

create index if not exists idx_concept_maps_user_id
  on public.concept_maps (user_id);

create index if not exists idx_concept_map_progress_user_map
  on public.concept_map_progress (user_id, map_id);

create policy if not exists documents_select_own_rows
  on public.documents
  for select
  using (auth.uid() = user_id);

create policy if not exists documents_insert_own_rows
  on public.documents
  for insert
  with check (auth.uid() = user_id);

create policy if not exists documents_update_own_rows
  on public.documents
  for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy if not exists documents_delete_own_rows
  on public.documents
  for delete
  using (auth.uid() = user_id);

create policy if not exists study_sessions_select_own_rows
  on public.study_sessions
  for select
  using (auth.uid() = user_id);

create policy if not exists study_sessions_insert_own_rows
  on public.study_sessions
  for insert
  with check (auth.uid() = user_id);

create policy if not exists study_sessions_update_own_rows
  on public.study_sessions
  for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy if not exists study_sessions_delete_own_rows
  on public.study_sessions
  for delete
  using (auth.uid() = user_id);

create policy if not exists notes_select_own_rows
  on public.notes
  for select
  using (auth.uid() = user_id);

create policy if not exists notes_insert_own_rows
  on public.notes
  for insert
  with check (auth.uid() = user_id);

create policy if not exists notes_update_own_rows
  on public.notes
  for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy if not exists notes_delete_own_rows
  on public.notes
  for delete
  using (auth.uid() = user_id);

create policy if not exists streaks_select_own_rows
  on public.streaks
  for select
  using (auth.uid() = user_id);

create policy if not exists streaks_insert_own_rows
  on public.streaks
  for insert
  with check (auth.uid() = user_id);

create policy if not exists streaks_update_own_rows
  on public.streaks
  for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- The application should only use user-scoped operations for document, note, and study data.
-- This migration preserves user isolation and does not delete any existing records.
