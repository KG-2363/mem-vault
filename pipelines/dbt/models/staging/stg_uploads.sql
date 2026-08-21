-- Cleans photo.uploaded events from the raw events table
with source as (
    select
        event_id,
        tenant_id,
        json_value(payload, '$.album_id')  as album_id,
        json_value(payload, '$.photo_id')  as photo_id,
        json_value(payload, '$.gcs_raw_path') as gcs_raw_path,
        event_timestamp                    as uploaded_at,
        ingested_at
    from {{ source('analytics_raw', 'events_raw') }}
    where event_type = 'photo.uploaded'
)

select * from source
