--droping existing pepys.dashboard_metadata function
drop function if exists pepys.dashboard_metadata;

--creating pepys.dashboard_metadata function
create function pepys.dashboard_metadata(
	ui_inp_start_date text,
	ui_inp_end_date text)
returns table (
	record_type text,
	serial_id uuid,
	platform_id uuid,
	"name" text,
	platform_type_name text,
	"start" timestamp without time zone,
	"end" timestamp without time zone,
	gap_seconds int)
as
$$
begin
	return query
with
latest_serials as (
	select 
		s.serial_id,
		s.serial_number::text serial_name,
		s.exercise,
		s.start serial_start,
		s.end serial_end
	from
		pepys."Serials" s
	where 
		s.start::date = to_date(ui_inp_start_date, 'YYYY-MM-DD')
			and
		s.end::date = to_date(ui_inp_end_date, 'YYYY-MM-DD')
),
participating_platforms as (
	select
		ep.platform_id,
		p.name::text platform_name,
		pt.default_data_interval_secs gap_seconds,
		pt.name::text platform_type_name,
		ls.serial_start,
		ls.serial_end,
		coalesce(sp.start, ls.serial_start) serial_participant_start,
		coalesce(sp.end, ls.serial_end) serial_participant_end,
		sp.serial_id
	from
		pepys."SerialParticipants" sp
			inner join
		pepys."WargameParticipants" ep
				on sp.wargame_participant_id = ep.wargame_participant_id
			inner join
		pepys."Platforms" p
				on p.platform_id = ep.platform_id
			inner join
		pepys."PlatformTypes" pt
				on p.platform_type_id = pt.platform_type_id
			inner join
		latest_serials ls
				on ls.serial_id = sp.serial_id
)
select
	'SERIALS' record_type,
	s.serial_id,
	NULL platform_id,
	s.serial_name "name",
	s.exercise,
	NULL platform_type_name,
	s.serial_start "start",
	s.serial_end "end",
	NULL gap_seconds
from
	latest_serials s
union all
select
	'SERIAL PARTICIPANT' record_type,
	pp.serial_id,
	pp.platform_id,
	pp.platform_name "name",
	NULL exercise,
	pp.platform_type_name,
	pp.serial_participant_start "start",
	pp.serial_participant_end "end",
	pp.gap_seconds
from
	participating_platforms pp
order by 
	record_type desc,
	"name",
	"start",
	"end";
end;
$$
language plpgsql;

