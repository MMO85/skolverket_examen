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
        performance_bucket,
        betygspoang_totalt,
        betygpoang_flickor,
        betygpoang_pojkar,
        betygpoang_gap_f_minus_m
    from {{ ref('mart_parent_choice_ak9') }}
),

trend as (
    select
        *,

        lag(score) over (
            partition by kommun, subject, huvudman_typ
            order by year
        ) as score_prev_year,

        lag(rank_sweden) over (
            partition by kommun, subject, huvudman_typ
            order by year
        ) as rank_sweden_prev_year,

        lag(rank_lan) over (
            partition by kommun, subject, huvudman_typ
            order by year
        ) as rank_lan_prev_year

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
    performance_bucket,

    score_prev_year,
    (score - score_prev_year) as score_change_yoy,

    rank_sweden_prev_year,
    (rank_sweden_prev_year - rank_sweden) as rank_sweden_change_yoy, -- مثبت یعنی بهتر شده

    rank_lan_prev_year,
    (rank_lan_prev_year - rank_lan) as rank_lan_change_yoy, -- مثبت یعنی بهتر شده

    case
        when score_prev_year is null then 'No previous year'
        when (score - score_prev_year) >= 2 then 'Improving'
        when (score - score_prev_year) <= -2 then 'Declining'
        else 'Stable'
    end as trend_label,

    betygspoang_totalt,
    betygpoang_flickor,
    betygpoang_pojkar,
    betygpoang_gap_f_minus_m

from trend
