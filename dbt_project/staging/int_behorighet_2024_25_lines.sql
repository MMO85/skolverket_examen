{{ config(materialized='table') }}

select distinct
  raw_line,
  source_file
from {{ source('staging_data', 'raw_data') }}
where source_file = 'behorighet_grundskola_2024_25.csv'
  and raw_line not like 'Statistik från Skolverket%'
  and raw_line not like 'Grundskola - Behörighet%'
  and raw_line not like 'Valt läsår:%'
  and raw_line not like 'Inför nya gymnasieskolan%'
  and raw_line not like 'Kommun;Kommun-kod;%'
  and raw_line like '%;%'
