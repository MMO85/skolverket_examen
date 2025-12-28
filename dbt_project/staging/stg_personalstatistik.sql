{{ config(materialized='table') }}

with filtered as (

    select *
    from {{ ref('stg_raw_data') }}
    where source_file like 'Grundskola - Personalstatistik med lärarlegitimation%'
      and raw_line like '%;%'
      and raw_line not like 'Kommun;Kommun-kod;%'
      and raw_line not like 'Statistik från Skolverket%'
      and raw_line not like 'Valt läsår:%'
      and raw_line not like 'Valt uttag:%'
      and raw_line not like 'Från och med läsåret%'

),

parsed as (

    select
        str_split(raw_line, ';') as p,
        source_file,
        cast(regexp_extract(source_file, '([0-9]{4})', 1) as int) as lasar_start
    from filtered
)

select
    lasar_start,

    p[1]  as kommun,
    p[2]  as kommun_kod,
    p[3]  as lan,
    p[4]  as lan_kod,
    p[5]  as huvudman_typ,

    -- Heltidstjänster (FTE)
    p[6]  as fte_totalt,
    p[7]  as fte_legitimerade,
    p[8]  as fte_andel_legitimerade,
    p[9]  as fte_forstelarare,

    -- Tjänstgörande lärare (headcount)
    p[10] as headcount_totalt,
    p[11] as headcount_legitimerade,
    p[12] as headcount_andel_legitimerade,
    p[13] as headcount_forstelarare,

    source_file

from parsed
