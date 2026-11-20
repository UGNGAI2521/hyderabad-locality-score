-- Hyderabad Locality Score: owner listings, enquiries and photos.
-- Owners sign in by email and post listings; every new or edited listing waits as 'pending'
-- until the site admin sets it to 'live' in the Supabase Table Editor.
-- Safe to re-run.

create table if not exists public.listings (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users on delete cascade,
  created_at timestamptz not null default now(),
  status text not null default 'pending' check (status in ('pending', 'live', 'closed')),
  mode text not null check (mode in ('buy', 'rent')),            -- 'buy' = for sale
  type text not null check (type in ('flat', 'house', 'villa', 'plot', 'office', 'shop')),
  locality text not null check (char_length(locality) between 2 and 60),
  title text not null check (char_length(title) between 5 and 120),
  bhk smallint not null default 0 check (bhk between 0 and 10),
  baths smallint not null default 0 check (baths between 0 and 10),
  area numeric not null check (area > 0 and area < 1000000),
  unit text not null default 'sqft' check (unit in ('sqft', 'sqyd')),
  price bigint not null check (price > 0 and price < 100000000000), -- rupees; rent is per month
  furnishing text not null default '' check (furnishing in ('', 'Unfurnished', 'Semi-furnished', 'Fully furnished', 'Bare shell')),
  ready text not null default 'Ready to move' check (ready in ('Ready to move', 'Under construction', 'Ready to register')),
  description text not null default '' check (char_length(description) <= 2000),
  photos text[] not null default '{}' check (cardinality(photos) <= 8)
);
create index if not exists listings_live on public.listings (status, created_at desc);

-- Kept apart from listings so a public read of a listing never exposes the owner's phone.
create table if not exists public.enquiries (
  id uuid primary key default gen_random_uuid(),
  listing_id uuid not null references public.listings on delete cascade,
  sender_id uuid not null default auth.uid() references auth.users on delete cascade,
  created_at timestamptz not null default now(),
  name text not null check (char_length(name) between 1 and 80),
  phone text not null check (phone ~ '^[6-9][0-9]{9}$'),
  message text not null default '' check (char_length(message) <= 1000)
);

alter table public.listings enable row level security;
alter table public.enquiries enable row level security;

drop policy if exists "anyone reads live listings, owners read their own" on public.listings;
create policy "anyone reads live listings, owners read their own" on public.listings
  for select using (status = 'live' or owner_id = auth.uid());

drop policy if exists "owners add pending listings" on public.listings;
create policy "owners add pending listings" on public.listings
  for insert to authenticated with check (owner_id = auth.uid() and status = 'pending');

-- An owner's edit sends the listing back for review (or closes it); only the admin makes it live.
drop policy if exists "owners edit their own listings" on public.listings;
create policy "owners edit their own listings" on public.listings
  for update to authenticated using (owner_id = auth.uid())
  with check (owner_id = auth.uid() and status in ('pending', 'closed'));

drop policy if exists "owners delete their own listings" on public.listings;
create policy "owners delete their own listings" on public.listings
  for delete to authenticated using (owner_id = auth.uid());

drop policy if exists "signed-in people enquire about live listings" on public.enquiries;
create policy "signed-in people enquire about live listings" on public.enquiries
  for insert to authenticated with check (
    sender_id = auth.uid()
    and exists (select 1 from public.listings l where l.id = listing_id and l.status = 'live' and l.owner_id <> auth.uid()));

drop policy if exists "owners and senders read enquiries" on public.enquiries;
create policy "owners and senders read enquiries" on public.enquiries
  for select to authenticated using (
    sender_id = auth.uid() or exists (select 1 from public.listings l where l.id = listing_id and l.owner_id = auth.uid()));

-- Photos: public to view; each owner uploads only into a folder named after their user id.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('listing-photos', 'listing-photos', true, 5242880, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do update set public = true, file_size_limit = 5242880, allowed_mime_types = array['image/jpeg', 'image/png', 'image/webp'];

drop policy if exists "owners upload listing photos to their folder" on storage.objects;
create policy "owners upload listing photos to their folder" on storage.objects
  for insert to authenticated with check (bucket_id = 'listing-photos' and (storage.foldername(name))[1] = auth.uid()::text);

-- Storage only deletes files the caller can also select, so owners need to see their own folder.
drop policy if exists "owners see their listing photos" on storage.objects;
create policy "owners see their listing photos" on storage.objects
  for select to authenticated using (bucket_id = 'listing-photos' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists "owners delete their listing photos" on storage.objects;
create policy "owners delete their listing photos" on storage.objects
  for delete to authenticated using (bucket_id = 'listing-photos' and (storage.foldername(name))[1] = auth.uid()::text);
