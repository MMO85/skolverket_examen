{{ config(materialized='view') }}

with base as (

    select
        raw_line,
        source_file,
        cast(regexp_extract(source_file, '([0-9]{4})', 1) as int) as lasar_start
    from {{ ref('stg_raw_data') }}
    where source_file like 'Grundskola - Resultat nationella prov årskurs 9%'

),

filtered as (

    -- فقط ردیف‌های دیتایی (نه توضیحات و نه هدر)
    select *
    from base
    where raw_line like '%;%'
      and raw_line not like 'Kommun;Kommun-kod;Län;Läns-kod;Typ av huvudman;Ämne;%'
      and raw_line not like 'Statistik från Skolverket%'
      and raw_line not like 'Grundskola - Resultat nationella prov%'
      and raw_line not like 'Valt läsår:%'
      and raw_line not like ';;;;;;Andel (%) elever som deltagit%'
      and raw_line not like 'Under vårterminen%'
      and raw_line not like 'Skolverket rekommenderade%'
      and raw_line not like 'För provbetyget%'

),

parsed as (

    select
        str_split(raw_line, ';') as p,
        lasar_start,
        source_file
    from filtered

),

final as (

    select
        lasar_start,

        p[1]  as kommun,
        p[2]  as kommun_kod,
        p[3]  as lan,
        p[4]  as lan_kod,
        p[5]  as huvudman_typ,
        p[6]  as amne,

        p[7]  as deltagit_totalt,
        p[8]  as deltagit_flickor,
        p[9]  as deltagit_pojkar,

        p[10] as antal_af_totalt,
        p[11] as antal_af_flickor,
        p[12] as antal_af_pojkar,

        p[13] as andel_ae_totalt,
        p[14] as andel_ae_flickor,
        p[15] as andel_ae_pojkar,

        p[16] as betygspoang_totalt,
        p[17] as betygspoang_flickor,
        p[18] as betygspoang_pojkar,

        source_file
    from parsed
    where p[6] in ('Engelska', 'Matematik', 'Svenska', 'Svenska som andraspråk')

)

select *
from final
