"""모든 팀 데이터 검증"""
import sys
sys.path.insert(0, '.')
from services.enriched_data_loader import EnrichedDomainDataLoader

loader = EnrichedDomainDataLoader()

teams = ['Arsenal', 'Liverpool', 'Man City', 'Chelsea']

print("\n" + "="*70)
print("팀 데이터 검증")
print("="*70)

for team_name in teams:
    print(f"\n{'#'*70}")
    print(f"# {team_name}")
    print(f"{'#'*70}")
    try:
        team_data = loader.load_team_data(team_name)
        print(f"\n✅ {team_name} loaded successfully!")
        print(f"   Formation: {team_data.formation}")
        players_with_ratings = sum(1 for p in team_data.lineup.values() if p.ratings)
        print(f"   Players with ratings: {players_with_ratings}/11")
        if team_data.team_strategy_commentary:
            print(f"   Team commentary: {team_data.team_strategy_commentary[:60]}...")
        if team_data.derived_strengths:
            ds = team_data.derived_strengths
            print(f"   Derived Strengths:")
            print(f"     Attack: {ds.attack_strength:.1f}/100")
            print(f"     Defense: {ds.defense_strength:.1f}/100")
            print(f"     Midfield: {ds.midfield_control:.1f}/100")
            print(f"     Physical: {ds.physical_intensity:.1f}/100")
            print(f"     Style: {ds.buildup_style}")
    except Exception as e:
        print(f"\n❌ {team_name} failed: {str(e)}")

print(f"\n{'='*70}")
print("✅ Validation complete!")
print(f"{'='*70}\n")
