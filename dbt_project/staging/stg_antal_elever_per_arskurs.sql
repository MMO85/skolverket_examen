{{ config(materialized='view') }}

with filtered as (

    select *
    from {{ ref('stg_raw_data') }}
    where source_file like 'Grundskola - Antal elever per årskurs%'
      and raw_line like '%;%'
      and raw_line not like 'Kommun;%'
      and raw_line not like 'Valt läsår:%'
      and raw_line not like 'Statistik från Skolverket%'

),

parsed as (

    select
        str_split(raw_line, ';') as p,
        source_file,
        -- سال را از نام فایل استخراج می‌کنیم (2020، 2021، ...)
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
    p[6]  as andel_flickor,
    p[7]  as andel_utlandsbakgrund,
    p[8]  as andel_hogutbildade_foraldrar,
    p[9]  as elever_ak1,
    p[10] as elever_ak2,
    p[11] as elever_ak3,
    p[12] as elever_ak4,
    p[13] as elever_ak5,
    p[14] as elever_ak6,
    p[15] as elever_ak7,
    p[16] as elever_ak8,
    p[17] as elever_ak9,
    p[18] as elever_totalt_1_9,
    source_file
from parsed
