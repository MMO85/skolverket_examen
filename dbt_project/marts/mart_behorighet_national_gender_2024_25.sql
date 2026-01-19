with base as (
  select *
  from {{ ref('stg_behorighet_2024_25') }}
  where kon in ('Flickor', 'Pojkar')
    and huvudman_typ = 'Samtliga'
),

agg as (
  select
    kon,

    (sum(behorig_yrkes * antal_elever) /
      nullif(sum(case when behorig_yrkes is not null then antal_elever end), 0)
    ) as yrkes_wavg,

    (sum(behorig_estet * antal_elever) /
      nullif(sum(case when behorig_estet is not null then antal_elever end), 0)
    ) as estet_wavg,

    (sum(behorig_eko_hum_sam * antal_elever) /
      nullif(sum(case when behorig_eko_hum_sam is not null then antal_elever end), 0)
    ) as eko_hum_sam_wavg,

    (sum(behorig_nat_tek * antal_elever) /
      nullif(sum(case when behorig_nat_tek is not null then antal_elever end), 0)
    ) as nat_tek_wavg

  from base
  group by 1
),

-- برای chart بهتر: wide -> long
final as (
  select kon, 'Yrkesprogram' as program, yrkes_wavg as behorighet_pct from agg
  union all
  select kon, 'Estetiskt'    as program, estet_wavg as behorighet_pct from agg
  union all
  select kon, 'Eko/Hum/Sam'  as program, eko_hum_sam_wavg as behorighet_pct from agg
  union all
  select kon, 'Natur/Teknik' as program, nat_tek_wavg as behorighet_pct from agg
)

select * from final
