{{ config(materialized='table') }}

select *
from (
  select
    *,
    row_number() over (
      partition by kommun_kod, huvudman_typ
      order by lasar_start desc
    ) as rn
  from {{ ref('mart_budget_per_elev_kommun') }}
) t
where rn = 1
