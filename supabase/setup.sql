-- Vigi-Track Simple: the database.
-- Paste this whole file in Supabase > SQL Editor > New query, then click Run.

-- 1. One row per report: which drug, which symptoms, an optional note.
create table if not exists reports (
  id         bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  drug       text   not null check (char_length(drug) between 1 and 80),
  symptoms   text[] not null check (cardinality(symptoms) between 1 and 15),
  note       text            check (char_length(note) <= 500)
);

-- Makes "all reports for this drug" fast.
create index if not exists reports_drug_idx on reports (drug);

-- 2. Security. With row level security on, nobody can do anything
--    unless a policy below allows it.
alter table reports enable row level security;

-- Visitors (the "anon" role, the public key in config.js) can read every report...
create policy "Anyone can read reports"
  on reports for select to anon
  using (true);

-- ...and add new ones. There is no policy for update or delete,
-- so visitors cannot change or remove anyone's report.
create policy "Anyone can add a report"
  on reports for insert to anon
  with check (true);
