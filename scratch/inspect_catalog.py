import pandas as pd

df = pd.read_csv('data/processed/Movies_Master_Cleaned.csv')
print('=== CATALOG OVERVIEW ===')
print('Total rows:', len(df))
print('Columns:', df.columns.tolist())

# Cast search for Vijay
cast_matches = df[df['cast'].str.contains('Vijay', case=False, na=False)]
print('\n=== VIJAY CAST MATCHES ===')
print('Total movies with Vijay in cast:', len(cast_matches))

vijay_names = set()
for c in cast_matches['cast']:
    for name in c.split(','):
        if 'vijay' in name.lower():
            vijay_names.add(name.strip())
print('\nActor variations containing Vijay:', sorted(list(vijay_names)))

thalapathy_matches = df[df['cast'].str.contains('Thalapathy', case=False, na=False)]
print('\nTotal movies with Thalapathy in cast:', len(thalapathy_matches))
if len(thalapathy_matches) > 0:
    for idx, row in thalapathy_matches.iterrows():
        print(f"  {row['catalog_id']} | {row['title']} | Cast: {row['cast']}")

# Check Tamil movies with Joseph Vijay or Vijay as lead:
print('\nSample Joseph Vijay / Vijay titles:')
for idx, row in cast_matches.head(15).iterrows():
    print(f"  {row['catalog_id']} | {row['title']} ({row['release_year']}) | {row['industry']} | {row['genre']} | Director: {row['director']} | Lead Cast: {row['cast'][:50]}")

print('\n=== ALL JOSEPH VIJAY MOVIES ===')
jv = df[df['cast'].str.contains('Joseph Vijay', case=False, na=False)]
print('Total movies with Joseph Vijay in cast:', len(jv))
for idx, r in jv.iterrows():
    print(f"  {r['catalog_id']} | {r['title']} ({r['release_year']}) | {r['industry']} | {r['genre']} | Dir: {r['director']} | Cast: {r['cast']}")

print('\n=== DIRECTOR SEARCH: Lokesh Kanagaraj ===')
lk = df[df['director'].str.contains('Lokesh', case=False, na=False)]
print('Total movies directed by Lokesh:', len(lk))
for idx, r in lk.iterrows():
    print(f"  {r['catalog_id']} | {r['title']} ({r['release_year']}) | {r['industry']} | {r['genre']} | Dir: {r['director']} | Cast: {r['cast']}")

print('\n=== BTS SEARCH ===')
bts = df[df['title'].str.contains('BTS', case=False, na=False) | df['cast'].str.contains('BTS', case=False, na=False)]
print('Total BTS matches in title or cast:', len(bts))
for idx, r in bts.iterrows():
    print(f"  {r['catalog_id']} | {r['title']} | Cast: {r['cast']}")
