{{ config(materialized='view') }}

with filtered as (

    select *
    from {{ ref('stg_raw_data') }}
    where source_file like 'Grundskola - Kostnader per kommun%'
      and raw_line like '%;%'
      and raw_line not like 'Kommun;Kommunkod;%'
      and raw_line not like 'Grundskola - Kostnader per kommun%'
      and raw_line not like 'Valt år:%'
      and raw_line not like 'Endast kommunal huvudman%'

),

parsed as (

    select
        str_split(raw_line, ';') as p,
        source_file,
        cast(regexp_extract(source_file, '([0-9]{4})', 1) as int) as year_start
    from filtered
)

select
    year_start,

    p[1]  as kommun,
    p[2]  as kommunkod,
    p[3]  as lan,
    p[4]  as lan_kod,
    p[5]  as huvudman_typ,

    p[6]  as genomsnittligt_elevantal,
    p[7]  as totalt,
    p[8]  as undervisning,
    p[9]  as totalt_per_elev,
    p[10] as undervisning_per_elev,
    p[11] as lokaler_per_elev,
    p[12] as maltider_per_elev,
    p[13] as larverktyg_per_elev,
    p[14] as elevhalsa_per_elev,
    p[15] as ovrigt_per_elev,

    source_file
from parsed
