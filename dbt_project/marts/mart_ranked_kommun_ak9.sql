{{ config(materialized='table') }}

with base as (
    select
        lasar_start,
        kommun,
        kommun_kod,
        lan,
        lan_kod,
        huvudman_typ,
        amne,
        betygspoang_totalt,
        betygspoang_flickor,
        betygspoang_pojkar,
        -- gap = girls - boys (only when both exist)
        case
            when betygspoang_flickor is not null and betygspoang_pojkar is not null
                then betygspoang_flickor - betygspoang_pojkar
            else null
        end as betygspoang_gap_f_minus_m
    from {{ ref('stg_nationella_prov_ak9_typed') }}
    where betygspoang_totalt is not null
),

kommun_agg as (
    select
        lasar_start,
        lan,
        lan_kod,
        huvudman_typ,
        amne,
        kommun,
        kommun_kod,
        avg(betygspoang_totalt) as avg_total,
        avg(betygspoang_flickor) as avg_flickor,
        avg(betygspoang_pojkar)  as avg_pojkar,
        avg(betygspoang_gap_f_minus_m) as avg_gap_f_minus_m,
        count(*) as n_rows
    from base
    group by 1,2,3,4,5,6,7
),

ranked as (
    select
        *,
        dense_rank() over (
            partition by lasar_start, huvudman_typ, amne
            order by avg_total desc
        ) as rank_in_sweden,
        count(*) over (
            partition by lasar_start, huvudman_typ, amne
        ) as n_kommun_sweden,
        percent_rank() over (
            partition by lasar_start, huvudman_typ, amne
            order by avg_total
        ) as pct_in_sweden,

        dense_rank() over (
            partition by lasar_start, lan_kod, huvudman_typ, amne
            order by avg_total desc
        ) as rank_in_lan,
        count(*) over (
            partition by lasar_start, lan_kod, huvudman_typ, amne
        ) as n_kommun_in_lan,
        percent_rank() over (
            partition by lasar_start, lan_kod, huvudman_typ, amne
            order by avg_total
        ) as pct_in_lan
    from kommun_agg
),

final as (
    select
        *,
        round(pct_in_sweden * 100, 1) as score_0_100
    from ranked
)

select *
from final
