{{ config(materialized='table') }}

with base as (
    select
        kommun,
        lan,
        year,
        subject,
        huvudman_typ,

        score,
        rank_sweden,
        rank_lan,

        betygspoang_totalt,
        betygpoang_flickor,
        betygpoang_pojkar,
        betygpoang_gap_f_minus_m
    from {{ ref('mart_parent_choice_ak9') }}
),

fairness as (
    select
        *,

        abs(betygpoang_gap_f_minus_m) as gap_abs,

        -- نرمال‌سازی عدالت در هر (year, subject, huvudman_typ) بر اساس max gap_abs
        max(abs(betygpoang_gap_f_minus_m)) over (
            partition by year, subject, huvudman_typ
        ) as max_gap_abs_group

    from base
)

select
    kommun,
    lan,
    year,
    subject,
    huvudman_typ,

    score,
    rank_sweden,
    rank_lan,

    betygspoang_totalt,
    betygpoang_flickor,
    betygpoang_pojkar,
    betygpoang_gap_f_minus_m,
    gap_abs,

    -- fairness_score: 100 بهترین (کمترین gap_abs)، 0 بدترین
    round(
        100.0 * (1.0 - gap_abs / nullif(max_gap_abs_group, 0.0))
    , 1) as fairness_score,

    -- رتبه عدالت در سوئد: 1 = عادلانه‌تر (gap_abs کمتر)
    dense_rank() over (
        partition by year, subject, huvudman_typ
        order by gap_abs asc
    ) as fairness_rank_sweden,

    -- رتبه عدالت داخل län
    dense_rank() over (
        partition by year, subject, huvudman_typ, lan
        order by gap_abs asc
    ) as fairness_rank_lan,

    case
        when gap_abs <= 1 then 'Balanced'
        when gap_abs <= 3 then 'Moderate gap'
        else 'High gap'
    end as fairness_label

from fairness