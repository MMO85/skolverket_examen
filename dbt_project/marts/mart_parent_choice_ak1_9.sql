{{ config(materialized='table') }}

with base as (
    select
        case
          when lasar_start between 1900 and 2100
            then lasar_start
          else cast(substr(cast(lasar_start as varchar), 1, 4) as integer)
        end as year,

        kommun,
        lan,

        case
          when lower(huvudman_typ) like '%enskild%' then 'Enskild'
          when lower(huvudman_typ) like '%kommunal%' then 'Kommunal'
          when lower(huvudman_typ) like '%samtliga%' then 'Samtliga'
          else huvudman_typ
        end as huvudman_typ,

        -- ✅ remove spaces like '3 631' then cast
        try_cast(replace(cast(elever_totalt_1_9 as varchar), ' ', '') as bigint) as n_students

    from {{ ref('stg_antal_elever_per_arskurs') }}
    where kommun is not null
      and lan is not null
      and huvudman_typ is not null
      and elever_totalt_1_9 is not null
),

filtered as (
    select
        year, kommun, lan, huvudman_typ, n_students
    from base
    where huvudman_typ in ('Kommunal', 'Enskild')
      and n_students is not null
      and n_students >= 0
),

totals as (
    select
        year, kommun, lan,
        sum(n_students) as n_total
    from filtered
    group by 1,2,3
)

select
    f.year,
    f.kommun,
    f.lan,
    f.huvudman_typ,
    f.n_students,
    t.n_total,
    case
        when t.n_total = 0 then 0.0
        else f.n_students * 1.0 / t.n_total
    end as share
from filtered f
inner join totals t
    on f.year = t.year
   and f.kommun = t.kommun
   and f.lan = t.lan