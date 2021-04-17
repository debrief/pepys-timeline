with 
serial_participants_input_json as (
	select 
		<spij_string_bind_variable>::json spij, -- Example:  '[ { "serial_id": "faa18ef7-6823-33dc-0f16-de6e4b2c02f3", "platform_id": "50d64387-9f91-4c6f-8933-f4e7b1a7d8ab", "start": "2020-11-15 00:00:00", "end": "2020-11-15 23:59:59", "gap_seconds": 30 } ]'
		<range_type_string_bind_variable>::json range_types 		-- Example: '[ "C", "G" ]'
),
range_types as (
	select
		json_array_elements_text(range_types) range_type
	from
		serial_participants_input_json
),
serial_participants_json as (
	select
		json_array_elements(spij) spj
	from
		serial_participants_input_json
),
participating_platforms as (
	select
		(spj->>'serial_id')::uuid serial_id,
		(spj->>'platform_id')::uuid platform_id,
		(spj->>'start')::timestamp serial_participant_start,
		(spj->>'end')::timestamp serial_participant_end,
		(spj->>'gap_seconds')::integer gap_seconds
	from
		serial_participants_json
),
sensors_involved as (
	select
		s.sensor_id,
		pp.platform_id,
		pp.gap_seconds,
		pp.serial_participant_start,
		pp.serial_participant_end,
		pp.serial_id
	from
		participating_platforms pp
			inner join
		pepys."Sensors" s
				on s.host = pp.platform_id
),
states_involved as (
	select 
		s.sensor_id,
		s.time
	from
		pepys."States" s
	where
		s.time >= (select 
					min(serial_participant_start) 
				from 
					participating_platforms)
			and
		s.time <= (select 
					max(serial_participant_end) 
				from 
					participating_platforms)
			and
		sensor_id in (select 
						sensor_id 
					from 
				sensors_involved)
),
state_time_rankings as (
	select 
		s.time, 
		row_number() over (partition by si.serial_id, si.platform_id order by s.time asc) as rowno,
		si.platform_id,
		si.gap_seconds,
		si.serial_id
	from 
		states_involved s
			inner join
		sensors_involved si
				on s.sensor_id = si.sensor_id
				and tsrange(si.serial_participant_start,
							si.serial_participant_end,
							'[]'
							) @> s.time
),
participation_sans_activity as (
	select
		si.serial_participant_start start_time,
		si.serial_participant_end end_time,
		si.platform_id,
		si.serial_id
	from
		sensors_involved si
	where
		not exists (select 1
					from 
						state_time_rankings s
					where 
						s.serial_id = si.serial_id
							and 
						s.platform_id = si.platform_id
							and
						tsrange(si.serial_participant_start,
								si.serial_participant_end,
								'[]'
								) @> s.time
				)
),
inner_gaps as (
	select
		s.time start_time,
		e.time end_time,
		s.platform_id,
		s.serial_id
	from
		state_time_rankings s
			inner join
		state_time_rankings e
				on s.platform_id=e.platform_id
				and s.serial_id=e.serial_id
				and s.rowno=e.rowno-1
				and e.time-s.time > 5 * s.gap_seconds *  interval '1 second'
),
edge_cases as ( --Identify boundary cases for all platform, serial combination
	select
		str.platform_id,
		str.serial_id,
		min(str.time) start_time, --Start
		max(str.time) end_time --End
	from
		state_time_rankings str
	group by
		str.platform_id,
		str.serial_id
),
gaps_at_serial_start as (
	select
		pp.serial_participant_start start_time,
		ec.start_time end_time,
		ec.platform_id,
		ec.serial_id
	from
		edge_cases ec
			inner join
		participating_platforms pp
				on ec.platform_id = pp.platform_id
				and ec.serial_id = pp.serial_id
				and ec.start_time - pp.serial_participant_start > 5 * pp.gap_seconds * interval '1 second'
),
gaps_at_serial_end as (
	select
		ec.end_time start_time,
		pp.serial_participant_end end_time,
		ec.platform_id,
		ec.serial_id
	from
		edge_cases ec
			inner join
		participating_platforms pp
				on ec.platform_id = pp.platform_id
				and ec.serial_id = pp.serial_id
				and pp.serial_participant_end - ec.end_time > 5 * pp.gap_seconds * interval '1 second'
),
consolidated_gaps as (
	select
		start_time,
		end_time,
		platform_id,
		serial_id
	from
		inner_gaps
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id
	from
		gaps_at_serial_start
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id
	from
		gaps_at_serial_end
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id
	from
		participation_sans_activity
),
consolidated_gap_ranks as (
	select
		start_time,
		end_time,
		platform_id,
		serial_id,
		row_number() over (partition by serial_id, platform_id order by start_time asc) as rowno
	from
		consolidated_gaps
),
participation_sans_gap as (
	select
		si.serial_participant_start start_time,
		si.serial_participant_end end_time,
		si.platform_id,
		si.serial_id
	from
		sensors_involved si
	where
		not exists (select 1
					from 
						consolidated_gaps cg
					where 
						si.serial_id = cg.serial_id
							and
						si.platform_id = cg.platform_id
							and 
						tsrange(si.serial_participant_start,
								si.serial_participant_end,
								'[]'
								) @> cg.start_time
				)
),
act_with_same_part_and_gap_start as (
	select
		cg.start_time,
		cg.start_time end_time,
		cg.platform_id,
		cg.serial_id
	from
		consolidated_gap_ranks cg
			inner join
		state_time_rankings s
				on cg.serial_id = s.serial_id
				and cg.platform_id = s.platform_id
				and cg.rowno = 1
				and cg.start_time =  s.time
			inner join
		sensors_involved si
				on si.serial_participant_start = cg.start_time
				and si.platform_id = cg.platform_id
				and si.serial_id = cg.serial_id
),
act_with_same_part_and_gap_end as (
	select
		cg.end_time start_time,
		cg.end_time,
		cg.platform_id,
		cg.serial_id
	from
		consolidated_gap_ranks cg
			inner join
		state_time_rankings s
				on cg.serial_id = s.serial_id
				and cg.platform_id = s.platform_id
				and cg.rowno = (select
									max(cgrs1.rowno)
								from
									consolidated_gap_ranks cgrs1
								where
									cgrs1.serial_id = cg.serial_id
										and
									cgrs1.platform_id = cg.platform_id)
				and cg.end_time =  s.time
			inner join
		sensors_involved si
				on si.serial_participant_start = cg.start_time
				and si.platform_id = cg.platform_id
				and si.serial_id = cg.serial_id
),
inner_coverage as (
	select
		cgrs.end_time start_time,
		cgre.start_time end_time,
		cgrs.platform_id,
		cgrs.serial_id
	from
		consolidated_gap_ranks cgrs
			inner join
		consolidated_gap_ranks cgre
				on cgrs.platform_id = cgre.platform_id
				and cgrs.serial_id = cgre.serial_id
				and cgrs.rowno=cgre.rowno-1
),
coverage_at_serial_start as (
	select
		pp.serial_participant_start start_time,
		cgrs.start_time end_time,
		cgrs.platform_id,
		cgrs.serial_id
	from
		consolidated_gap_ranks cgrs
			inner join
		participating_platforms pp
				on cgrs.platform_id = pp.platform_id
				and cgrs.serial_id = pp.serial_id
				and cgrs.rowno = 1
				and cgrs.start_time != pp.serial_participant_start
),
coverage_at_serial_end as (
	select
		cgrs.end_time start_time,
		pp.serial_participant_end end_time,
		cgrs.platform_id,
		cgrs.serial_id
	from
		consolidated_gap_ranks cgrs
			inner join
		participating_platforms pp
				on cgrs.platform_id = pp.platform_id
				and cgrs.serial_id = pp.serial_id
				and cgrs.rowno = (select
									max(cgrs1.rowno)
								from
									consolidated_gap_ranks cgrs1
								where
									cgrs1.serial_id = cgrs.serial_id
										and
									cgrs1.platform_id = cgrs.platform_id)
				and pp.serial_participant_end != cgrs.end_time
),
consolidated_coverage as (
	select
		start_time,
		end_time,
		platform_id,
		serial_id
	from
		inner_coverage ic
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id
	from
		coverage_at_serial_start
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id
	from
		coverage_at_serial_end
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id
	from
		participation_sans_gap
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id
	from
		act_with_same_part_and_gap_start
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id
	from
		act_with_same_part_and_gap_end
),
consolidated_stats as (
	select 
		'C' range_type,
		start_time,
		end_time,
		platform_id,
		serial_id
	from
		consolidated_coverage
	union all
	select 
		'G' range_type,
		start_time,
		end_time,
		platform_id,
		serial_id
	from
		consolidated_gaps
)
select
	range_type,
	start_time,
	end_time,
	platform_id,
	serial_id,
	to_char(end_time-start_time, 'HH24:MI:SS') delta
from
	consolidated_stats
where
	range_type in (select
					range_type
				from
					range_types)
order by
	serial_id asc,
	platform_id asc,
	start_time asc,
	end_time asc;

