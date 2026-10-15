# GLQS shares one main location across features

GLQS 0.39.0 is a Girl Life cheat mod assembled from 30 source fragments into five QSP locations. Fourteen feature screens share `mod_GLQS_main`, with `start` as their Index. This page records local source inspection on 2026-10-14 at GLQS commit `6de0a2ce7081a1e4275bffef39c2e86cc65e3b54`; it does not claim gameplay validation. ([01_setup.qsps:3](../../../src/01_setup.qsps#L3), [02_readme.qsps:4](../../../src/02_readme.qsps#L4), [build_support.py:13](../../../build_support.py#L13))

## Explicit manifests control source assembly

`STANDALONE_FILES` lists three fragments, and `SHARED_FILES` lists 27 in assembly order. The source has 3,153 physical lines; generated navigation and clothing actions bring the assembled file to 3,331 lines. Filename numbering groups related files but does not determine build order. The collector rejects missing or unlisted fragments. ([build_support.py:13](../../../build_support.py#L13), [build_support.py:93](../../../build_support.py#L93), [build_support.py:304](../../../build_support.py#L304))

The emitted locations are `mod_GLQS_setup`, `mod_GLQS_readme`, `mod_GLQS`, `mod_GLQS_options` and `mod_GLQS_main`. The hook fragment contains two locations, so the three standalone files produce four standalone locations. Feature fragments contain route bodies without wrappers; assembly adds one wrapper around their combined main location. ([03_hook.qsps:1](../../../src/03_hook.qsps#L1), [03_hook.qsps:57](../../../src/03_hook.qsps#L57), [build_support.py:309](../../../build_support.py#L309))

## Shared data drives menus and bulk actions

The navigation table defines clothing, body mods, skills, health, academics, magic, relationships, fame, money, jobs, housing, consumables, lifestyle and recurrent cheats. Both navigation modes read that registry. A scan using the repository's own regex extractors counted 61 distinct route definitions and 61 distinct static called route names; this measures recognized source forms rather than a parsed control-flow graph. ([04_main_menu.qsps:11](../../../src/04_main_menu.qsps#L11), [04_main_menu.qsps:126](../../../src/04_main_menu.qsps#L126), [build_support.py:134](../../../build_support.py#L134))

| Metadata | Literal row count | Source |
|---|---:|---|
| Clothing categories | 82 across 18 stores | [05_clothing_data.qsps:10](../../../src/05_clothing_data.qsps#L10) |
| Picker sort/filter definitions | 38: 17 sort, 21 filter | [05_clothing_filter_data.qsps:13](../../../src/05_clothing_filter_data.qsps#L13) |
| Consumables | 87: 51 stack, 36 single | [06_consumables_data.qsps:7](../../../src/06_consumables_data.qsps#L7) |
| Stats | 51: 50 level, 1 cap | [07_stats_data.qsps:9](../../../src/07_stats_data.qsps#L9) |
| Primary recurrent cheats | 20: 17 direct flags, 3 special handlers | [08_recurrent_data.qsps:13](../../../src/08_recurrent_data.qsps#L13) |
| School subjects | 13 | [09_grades_data.qsps:5](../../../src/09_grades_data.qsps#L5) |
| Fixed relationship roster | 110 across 10 categories | [11_relationships_data.qsps:19](../../../src/11_relationships_data.qsps#L19) |
| Tattoo/piercing zones | 26: 18 tattoo, 8 piercing | [12_bodymod.qsps:85](../../../src/12_bodymod.qsps#L85) |
| Fame entries and regions | 17 entries, 4 regions | [14_fame_data.qsps:8](../../../src/14_fame_data.qsps#L8) |
| Jobs | 28 | [17_jobs_data.qsps:4](../../../src/17_jobs_data.qsps#L4) |

These counts include literal metadata append rows, not generated NPCs or individual clothing items supplied by Girl Life. `split_row` writes its fields into shared `$glqs_field` scratch state, so callers copy fields before another split. Data fragments precede their consumers in the manifest. ([04_main_menu.qsps:28](../../../src/04_main_menu.qsps#L28), [build_support.py:19](../../../build_support.py#L19))

## GLQS research extends an inherited reference

The shared QSP, engine and Girl Life pages were copied from GLSS research dated 2026-10-14. Their pinned sources, historical GLSS examples and old validation remain inherited evidence. These four GLQS pages add local inspection, a pinned upstream comparison and current build results. Read [build and validation](build-and-validation.md) for executed checks, [gameplay integration](gameplay-integration.md) for upstream contracts, and [implementation observations](implementation-observations.md) for limits and unresolved behavior.
