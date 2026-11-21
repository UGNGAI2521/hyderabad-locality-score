-- Hyderabad Locality Score: resident notes and the early-access list.
-- NOT applied yet. Run this once in the Supabase SQL editor to switch both features on.
-- Resident notes: anyone can send one; it waits as 'pending' until the site admin sets it to 'live'
-- in the Supabase Table Editor, and only 'live' notes can be read by the public.
-- Early-access list: anyone can add an email; nobody can read the list through the site (the admin reads it in the Table Editor).
-- Safe to re-run.

create table if not exists public.locality_reviews (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  status text not null default 'pending' check (status in ('pending', 'live', 'rejected')),
  locality text not null check (char_length(locality) between 2 and 60),
  rating smallint not null check (rating between 1 and 5),
  body text not null check (char_length(body) between 20 and 600),
  author text not null check (char_length(author) between 1 and 40)
);
create index if not exists locality_reviews_live on public.locality_reviews (status, created_at desc);

create table if not exists public.waitlist (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  email text not null check (char_length(email) <= 200 and email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  locality text not null default '' check (char_length(locality) <= 60)
);
create unique index if not exists waitlist_email_once on public.waitlist (lower(email));

alter table public.locality_reviews enable row level security;
alter table public.waitlist enable row level security;

-- Visitors get only what the policies below allow: no update, no delete, no reading the waitlist.
revoke all on public.locality_reviews, public.waitlist from anon, authenticated;
grant select, insert on public.locality_reviews to anon, authenticated;
grant insert on public.waitlist to anon, authenticated;

drop policy if exists "anyone reads live notes" on public.locality_reviews;
create policy "anyone reads live notes" on public.locality_reviews
  for select using (status = 'live');

drop policy if exists "anyone sends a pending note" on public.locality_reviews;
create policy "anyone sends a pending note" on public.locality_reviews
  for insert with check (status = 'pending');

drop policy if exists "anyone joins the waitlist" on public.waitlist;
create policy "anyone joins the waitlist" on public.waitlist
  for insert with check (true);
