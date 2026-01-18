{{ config(materialized='view') }}

with src as (
    select *
    from {{ ref('stg_antal_elever_per_arskurs') }}
),

clean as (
    select
        lasar_start,
        kommun,
        kommun_kod,
        lan,
        lan_kod,
        huvudman_typ,

        -- درصدها (ممکنه عدد صحیح باشن یا اعشاری)
        try_cast(replace(andel_flickor, ',', '.') as double) as andel_flickor,
        try_cast(replace(andel_utlandsbakgrund, ',', '.') as double) as andel_utlandsbakgrund,
        try_cast(replace(andel_hogutbildade_foraldrar, ',', '.') as double) as andel_hogutbildade_foraldrar,

        -- اعداد دانش‌آموزان: حذف فاصله‌ها مثل "3 877"
        try_cast(replace(elever_ak1, ' ', '') as integer) as elever_ak1,
        try_cast(replace(elever_ak2, ' ', '') as integer) as elever_ak2,
        try_cast(replace(elever_ak3, ' ', '') as integer) as elever_ak3,
        try_cast(replace(elever_ak4, ' ', '') as integer) as elever_ak4,
        try_cast(replace(elever_ak5, ' ', '') as integer) as elever_ak5,
        try_cast(replace(elever_ak6, ' ', '') as integer) as elever_ak6,
        try_cast(replace(elever_ak7, ' ', '') as integer) as elever_ak7,
        try_cast(replace(elever_ak8, ' ', '') as integer) as elever_ak8,
        try_cast(replace(elever_ak9, ' ', '') as integer) as elever_ak9,
        try_cast(replace(elever_totalt_1_9, ' ', '') as integer) as elever_totalt_1_9,

        source_file
    from src
)

select * from clean
