{{ config(materialized='table') }}

with src as (
    select *
    from {{ ref('stg_nationella_prov_ak9') }}
),

clean as (
    select
        lasar_start,
        kommun,
        kommun_kod,
        lan,
        lan_kod,
        huvudman_typ,
        amne,

        -- helper: تبدیل ".." به NULL و "~100" به "100" و کاما به نقطه
        nullif(replace(replace(deltagit_totalt, '~', ''), ',', '.'), '..') as deltagit_totalt_s,
        nullif(replace(replace(deltagit_flickor, '~', ''), ',', '.'), '..') as deltagit_flickor_s,
        nullif(replace(replace(deltagit_pojkar, '~', ''), ',', '.'), '..') as deltagit_pojkar_s,

        nullif(replace(replace(andel_ae_totalt, '~', ''), ',', '.'), '..') as andel_ae_totalt_s,
        nullif(replace(replace(andel_ae_flickor, '~', ''), ',', '.'), '..') as andel_ae_flickor_s,
        nullif(replace(replace(andel_ae_pojkar, '~', ''), ',', '.'), '..') as andel_ae_pojkar_s,

        nullif(replace(replace(betygspoang_totalt, '~', ''), ',', '.'), '..') as betygspoang_totalt_s,
        nullif(replace(replace(betygspoang_flickor, '~', ''), ',', '.'), '..') as betygspoang_flickor_s,
        nullif(replace(replace(betygspoang_pojkar, '~', ''), ',', '.'), '..') as betygspoang_pojkar_s,

        -- counts معمولاً integer هستن؛ ".." رو NULL کن
        nullif(replace(antal_af_totalt, ' ', ''), '..') as antal_af_totalt_s,
        nullif(replace(antal_af_flickor, ' ', ''), '..') as antal_af_flickor_s,
        nullif(replace(antal_af_pojkar, ' ', ''), '..') as antal_af_pojkar_s,

        source_file
    from src
)

select
    lasar_start,
    kommun,
    kommun_kod,
    lan,
    lan_kod,
    huvudman_typ,
    amne,

    try_cast(deltagit_totalt_s as double) as deltagit_totalt,
    try_cast(deltagit_flickor_s as double) as deltagit_flickor,
    try_cast(deltagit_pojkar_s as double) as deltagit_pojkar,

    try_cast(antal_af_totalt_s as integer) as antal_af_totalt,
    try_cast(antal_af_flickor_s as integer) as antal_af_flickor,
    try_cast(antal_af_pojkar_s as integer) as antal_af_pojkar,

    try_cast(andel_ae_totalt_s as double) as andel_ae_totalt,
    try_cast(andel_ae_flickor_s as double) as andel_ae_flickor,
    try_cast(andel_ae_pojkar_s as double) as andel_ae_pojkar,

    try_cast(betygspoang_totalt_s as double) as betygspoang_totalt,
    try_cast(betygspoang_flickor_s as double) as betygspoang_flickor,
    try_cast(betygspoang_pojkar_s as double) as betygspoang_pojkar,

    source_file
from clean
