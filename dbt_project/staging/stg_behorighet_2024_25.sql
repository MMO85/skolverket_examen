with lines as (
  select raw_line
  from {{ ref('int_behorighet_2024_25_lines') }}
),

split as (
  select
    trim(split_part(raw_line, ';', 1))  as kommun,
    trim(split_part(raw_line, ';', 2))  as kommun_kod,
    trim(split_part(raw_line, ';', 3))  as lan,
    trim(split_part(raw_line, ';', 4))  as lans_kod,
    trim(split_part(raw_line, ';', 5))  as huvudman_typ,
    trim(split_part(raw_line, ';', 6))  as kon,
    trim(split_part(raw_line, ';', 7))  as antal_elever_raw,

    trim(split_part(raw_line, ';', 8))  as yrkes_raw,
    trim(split_part(raw_line, ';', 9))  as estet_raw,
    trim(split_part(raw_line, ';',10))  as eko_hum_sam_raw,
    trim(split_part(raw_line, ';',11))  as nat_tek_raw
  from lines
),

clean as (
  select
    kommun,
    kommun_kod,
    lan,
    lans_kod,
    huvudman_typ,
    kon,

    case
  when trim(antal_elever_raw) in ('', '..', '.') then null
  else cast(
    replace(
      replace(trim(antal_elever_raw), ' ', ''),
      chr(160), ''
    ) as integer
  )
end as antal_elever,
    -- تبدیل ~100 => 100
    -- حذف .. و . و خالی => null
    -- تبدیل decimal comma => decimal point
    case
      when yrkes_raw = '~100' then 100.0
      when yrkes_raw in ('..', '.', '') then null
      else cast(replace(yrkes_raw, ',', '.') as double)
    end as behorig_yrkes,

    case
      when estet_raw = '~100' then 100.0
      when estet_raw in ('..', '.', '') then null
      else cast(replace(estet_raw, ',', '.') as double)
    end as behorig_estet,

    case
      when eko_hum_sam_raw = '~100' then 100.0
      when eko_hum_sam_raw in ('..', '.', '') then null
      else cast(replace(eko_hum_sam_raw, ',', '.') as double)
    end as behorig_eko_hum_sam,

    case
      when nat_tek_raw = '~100' then 100.0
      when nat_tek_raw in ('..', '.', '') then null
      else cast(replace(nat_tek_raw, ',', '.') as double)
    end as behorig_nat_tek

  from split

  -- یک فیلتر محافظتی: ردیف‌های خراب/کوتاه رو حذف کن
  where kommun is not null
    and kommun <> ''
    and kon in ('Flickor', 'Pojkar', 'Samtliga')
    and huvudman_typ in ('Samtliga', 'Kommunal', 'Enskild')
)

select * from clean
