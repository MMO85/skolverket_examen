{{ config(materialized='table') }}

with src as (

    select
        lasar_start,
        kommun,
        kommun_kod,
        lan,
        lan_kod,
        huvudman_typ,
        amne,

        deltagit_totalt,
        deltagit_flickor,
        deltagit_pojkar,

        antal_af_totalt,
        antal_af_flickor,
        antal_af_pojkar,

        andel_ae_totalt,
        andel_ae_flickor,
        andel_ae_pojkar,

        betygspoang_totalt,
        betygspoang_flickor,
        betygspoang_pojkar,

        source_file
    from {{ ref('stg_nationella_prov_ak9_typed') }}

),

final as (

    select
        -- Grain: year x kommun x huvudman x ämne
        lasar_start,
        kommun,
        kommun_kod,
        lan,
        lan_kod,
        huvudman_typ,
        amne,

        -- participation (%)
        deltagit_totalt,
        deltagit_flickor,
        deltagit_pojkar,

        -- counts A-F
        antal_af_totalt,
        antal_af_flickor,
        antal_af_pojkar,

        -- share A-E (%)
        andel_ae_totalt,
        andel_ae_flickor,
        andel_ae_pojkar,

        -- grade points
        betygspoang_totalt,
        betygspoang_flickor,
        betygspoang_pojkar,

        -- derived metrics
        (betygspoang_flickor - betygspoang_pojkar) as betygspoang_gap_f_minus_m,

        source_file

    from src
)

select * from final
