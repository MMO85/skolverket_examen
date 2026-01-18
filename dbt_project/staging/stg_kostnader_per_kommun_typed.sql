{{ config(materialized='view') }}

with src as (
    select *
    from {{ ref('stg_kostnader_per_kommun') }}
)

select
    year_start,
    kommun,
    kommunkod,
    lan,
    lan_kod,
    huvudman_typ,

    try_cast(replace(genomsnittligt_elevantal, ' ', '') as integer) as genomsnittligt_elevantal,
    try_cast(replace(totalt, ' ', '') as integer) as totalt,
    try_cast(replace(undervisning, ' ', '') as integer) as undervisning,

    try_cast(replace(totalt_per_elev, ' ', '') as integer) as totalt_per_elev,
    try_cast(replace(undervisning_per_elev, ' ', '') as integer) as undervisning_per_elev,
    try_cast(replace(lokaler_per_elev, ' ', '') as integer) as lokaler_per_elev,
    try_cast(replace(maltider_per_elev, ' ', '') as integer) as maltider_per_elev,
    try_cast(replace(larverktyg_per_elev, ' ', '') as integer) as larverktyg_per_elev,
    try_cast(replace(elevhalsa_per_elev, ' ', '') as integer) as elevhalsa_per_elev,
    try_cast(replace(ovrigt_per_elev, ' ', '') as integer) as ovrigt_per_elev,

    source_file
from src
