{{ config(materialized='view') }}

with src as (
    select *
    from {{ ref('stg_personalstatistik') }}
)

select
    lasar_start,
    kommun,
    kommun_kod,
    lan,
    lan_kod,
    huvudman_typ,

    -- Heltidstjänster (FTE)
    try_cast(replace(fte_totalt, ',', '.') as double) as fte_totalt,
    try_cast(replace(fte_legitimerade, ',', '.') as double) as fte_legitimerade,
    try_cast(replace(fte_andel_legitimerade, ',', '.') as double) as fte_andel_legitimerade,
    try_cast(replace(fte_forstelarare, ',', '.') as double) as fte_forstelarare,

    -- Tjänstgörande lärare
    try_cast(replace(headcount_totalt, ',', '.') as double) as headcount_totalt,
    try_cast(replace(headcount_legitimerade, ',', '.') as double) as headcount_legitimerade,
    try_cast(replace(headcount_andel_legitimerade, ',', '.') as double) as headcount_andel_legitimerade,
    try_cast(replace(headcount_forstelarare, ',', '.') as double) as headcount_forstelarare,

    source_file

from src
