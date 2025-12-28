{{ config(materialized='table') }}

with base as (
    select
        case
          when lasar_start between 1900 and 2100
            then lasar_start
          else cast(substr(cast(lasar_start as varchar), 1, 4) as integer)
        end as year,

        kommun,
        lan,
        huvudman_typ,
        amne as subject,

        cast(betygspoang_totalt as double) as betygspoang_totalt,
        cast(betygspoang_flickor as double) as betygpoang_flickor,
        cast(betygspoang_pojkar as double) as betygpoang_pojkar,
        cast(betygspoang_flickor as double) - cast(betygspoang_pojkar as double) as betygpoang_gap_f_minus_m

    from {{ ref('stg_nationella_prov_ak9_typed') }}
    where kommun is not null
      and lan is not null
      and huvudman_typ is not null
      and amne is not null
      and betygspoang_totalt is not null
),

final_grain as (
    -- سطح subject
    select
        year, kommun, lan, huvudman_typ, subject,
        betygspoang_totalt, betygpoang_flickor, betygpoang_pojkar, betygpoang_gap_f_minus_m
    from base

    union all

    -- ALL = میانگین ساده همه subject ها
    select
        year,
        kommun,
        lan,
        huvudman_typ,
        'ALL' as subject,
        avg(betygspoang_totalt) as betygspoang_totalt,
        avg(betygpoang_flickor) as betygpoang_flickor,
        avg(betygpoang_pojkar) as betygpoang_pojkar,
        avg(betygpoang_flickor) - avg(betygpoang_pojkar) as betygpoang_gap_f_minus_m
    from base
    group by 1,2,3,4
),

scored as (
    select
        year,
        kommun,
        lan,
        huvudman_typ,
        subject,

        betygspoang_totalt,
        betygpoang_flickor,
        betygpoang_pojkar,
        betygpoang_gap_f_minus_m,

        round(
            100.0 * cume_dist() over (
                partition by year, subject, huvudman_typ
                order by betygspoang_totalt
            ), 1
        ) as score,

        dense_rank() over (
            partition by year, subject, huvudman_typ
            order by betygspoang_totalt desc
        ) as rank_sweden,

        dense_rank() over (
            partition by year, subject, huvudman_typ, lan
            order by betygspoang_totalt desc
        ) as rank_lan,

        case
          when round(
                 100.0 * cume_dist() over (
                     partition by year, subject, huvudman_typ
                     order by betygspoang_totalt
                 ), 1
               ) >= 90 then 'Top 10%'
          when round(
                 100.0 * cume_dist() over (
                     partition by year, subject, huvudman_typ
                     order by betygspoang_totalt
                 ), 1
               ) >= 50 then 'Middle'
          else 'Bottom 50%'
        end as performance_bucket

    from final_grain
)

select
    kommun,
    lan,
    year,
    subject,
    huvudman_typ,

    score,
    performance_bucket,
    rank_sweden,
    rank_lan,

    betygspoang_totalt,
    betygpoang_flickor,
    betygpoang_pojkar,
    betygpoang_gap_f_minus_m
from scored
