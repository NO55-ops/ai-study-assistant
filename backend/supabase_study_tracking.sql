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
