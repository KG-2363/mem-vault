-- Cleans photo.enhanced events
with source as (
    select
        event_id,
        tenant_id,
        json_value(payload, '$.album_id')        as album_id,
        json_value(payload, '$.photo_id')        as photo_id,
        json_value(payload, '$.gcs_enhanced_path') as gcs_enhanced_path,
        event_timestamp                          as enhanced_at,
        ingested_at
    from {{ source('analytics_raw', 'events_raw') }}
    where event_type = 'photo.enhanced'
)

select * from source
