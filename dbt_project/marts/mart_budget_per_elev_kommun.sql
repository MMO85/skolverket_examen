{{ config(materialized='table') }}

with src as (
    select
        year_start as lasar_start,
        kommun,
        lpad(cast(kommunkod as varchar), 4, '0') as kommun_kod,
        lan,
        lan_kod,
        huvudman_typ,

        genomsnittligt_elevantal,

        totalt,
        undervisning,

        totalt_per_elev,
        undervisning_per_elev,
        lokaler_per_elev,
        maltider_per_elev,
        larverktyg_per_elev,
        elevhalsa_per_elev,
        ovrigt_per_elev,

        source_file
    from {{ ref('stg_kostnader_per_kommun_typed') }}
),

filtered as (
    select *
    from src
    where totalt_per_elev is not null
),

dedup as (
    select *
    from (
        select
            *,
            row_number() over (
                partition by kommun_kod, lasar_start, huvudman_typ
                order by source_file desc
            ) as rn
        from filtered
    ) t
    where rn = 1
)

select
    lasar_start,
    kommun,
    kommun_kod,
    lan,
    lan_kod,
    huvudman_typ,

    genomsnittligt_elevantal,

    totalt,
    undervisning,

    totalt_per_elev,
    undervisning_per_elev,
    lokaler_per_elev,
    maltider_per_elev,
    larverktyg_per_elev,
    elevhalsa_per_elev,
    ovrigt_per_elev,

    source_file
from dedup
