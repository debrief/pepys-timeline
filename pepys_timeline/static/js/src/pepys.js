moment.locale("en");

const DATETIME_FORMAT = "YYYY-MM-DD HH:mm:ss";

let generatedCharts = false;
let charts = [];
let chartOptions = [];
let serialsMeta = [];
let serialsStats = [];

const defaultOptions = {
    margin: {
        right: 60,
        left: 50,
        top: 30,
        bottom: 0
    },
    padding: {
        top: 0,
        bottom: 0,
        right: 45,
        left: 2
    },
    reduce_space_wrap: 2000000000,
    title: {
        enabled: false
    },
    sub_title: {
        enabled: false
    },
    legend: {
        enabled: false
    },
    y_title_tooltip: {
        enabled: false
    },

    icon: {
        class_has_data: 'fas fa-fw fa-check',
        class_has_no_data: 'fas fa-fw fa-exclamation-circle'
    },
    responsive: {
        enabled: false,
    },
    line_spacing: 3,
    ticks_for_graph: 2,
    graph: {
        height: 35
    },
    y_percentage: {
        enabled: true,
        custom_percentage: true
    },
    responsive: {
        enabled: true
    }
};


function onDataReceived() {
    console.log('on data received');
}

function fetchConfig() {
    fetch('/config')
        .then(response => response.json())
        .then(response => {
            const { frequency_secs } = response;
            fetchSerials();
            fetchSerialsMeta();
            setInterval(fetchSerials, frequency_secs * 100);

        })
        .catch(err => console.error(err));
}

function fetchSerials() {
    console.log('fetching serials');
    fetch('/timelines')
      .then(response => response.json())
      .then(response => {
        const { serials } = response;
        //renderCharts(serials);
      })
      .catch(err => console.error(err));
}

function fetchSerialsMeta() {
    console.log('fetching serials metadata');

    const url = new URL(window.location + 'dashboard_metadata');
    const queryParams = new URLSearchParams();
    queryParams.set('from_date', '2021-01-05');
    queryParams.set('to_date', '2021-01-05');
    url.search = queryParams.toString();

    fetch(url)
      .then(response => response.json())
      .then(response => {
        const { dashboard_metadata } = response;
        console.log('testing dashboard_metadata', response);
        serialsMeta = dashboard_metadata;
        fetchSerialsStats();
      }
    )
}

function fetchSerialsStats() {
  const serialParticipants = serialsMeta.filter(m => m.record_type === "SERIAL PARTICIPANT");
  const range_types = ["G", "C"];

  let url = new URL(window.location + 'dashboard_stats');
  let queryParams = new URLSearchParams();
  queryParams.set('serial_participants', JSON.stringify(serialParticipants));
  queryParams.set('range_types', JSON.stringify(range_types));
  url.search = queryParams.toString();

  fetch(url)
    .then(response => response.json())
    .then(response => {
        console.log('testing dashboard_stats', response);
        const { dashboard_stats } = response;
        serialsStats = dashboard_stats;
        renderTimelines();
    })
}

function calculatePercentageClass(number) {
    switch (true) {

        case number <= 25:
            return "red";
            break;
        case number <= 60:
            return "amber";
            break;
        case number <= 100:
            return "green";
            break;
        default:
            return "ypercentage";

    };
}

function addChartDiv(index, header, header_class) {
    var newDiv = document.createElement('div');
    htmlString = '<div class="card"><div class="card-header text-center '+header_class+'"><h5>'+header+'</h5></div><div style="overflow: hidden;" class="visavail" id="visavail_container_new_'+index+'"><p id="visavail_graph_new_'+index+'"></p></div></div>'
    newDiv.innerHTML = htmlString.trim();
    newDiv.classList.add("col-md-3")
    newDiv.classList.add("col-xl-2")
    newDiv.classList.add("p-1")

    var currentDiv = document.getElementById("chart_row");
    currentDiv.appendChild(newDiv);
}

function transformSerials(serials) {
    const transformedData = serials.map(serial => {
        return serial.participants.map(participant => {
            // overall coverage
            const overall = [];
            for (let index = 0; index < participant.coverage.length; index++) {
                if (index != 0) {
                    if (new Date(participant.coverage[index - 1][1]).getTime() < new Date(participant.coverage[index][0]).getTime()) {
                        overall.push([participant.coverage[index - 1][1], 0, participant.coverage[index][0]]);
                    }
                } else {
                    overall.push([serial.start_time, 0, participant.coverage[index][1]]);
                }
                overall.push([participant.coverage[index][0], 1, participant.coverage[index][1]]);
            }
            const data = overall;
            return {
                measure: participant.name,
                icon: {
                    url: getParticipantIconUrl(participant),
                    width: 32,
                    height: 32,
                    padding: {
                        left: 0,
                        right: 8
                    },
                    background_class: participant["platform-type"].toLowerCase()
                },
                percentage: {
                    measure: participant["percent-coverage"] + " %",
                    class: "ypercentage_" + calculatePercentageClass(participant["percent-coverage"])
                },
                data: data
            }
        })
    })
    return transformedData;
}

function transformSerials2() {
    const serials = serialsMeta.filter(m => m.record_type === "SERIALS");
    const participants = serialsMeta.filter(m => m.record_type === "SERIAL PARTICIPANT");

    const transformedData = serials.map(serial => {
        let currSerialParticipants = participants.filter(p => p.serial_id === serial.serial_id);
        currSerialParticipants = currSerialParticipants.map(participant => {
            participant.serial_name = serial.name;
            participantStats = serialsStats.filter(
                s => s.resp_platform_id === participant.platform_id
                && s.resp_serial_id === participant.serial_name
            )
            let periods = participantStats.map(s => ([
                    moment(s.resp_start_time).format(DATETIME_FORMAT),
                    Number(s.resp_range_type === "C"),
                    moment(s.resp_end_time).format(DATETIME_FORMAT),
                ]));
            participant.coverage = periods;

            const totalParticipation = participantStats
                .map(s => new Date(s.resp_end_time) - new Date(s.resp_start_time))
                .reduce((s, d) => s + d, 0);
            const totalCoverage = participantStats
                .filter(s => s.resp_range_type === "C")
                .map(s => new Date(s.resp_end_time) - new Date(s.resp_start_time))
                .reduce((s, d) => s + d, 0);
            participant["percent-coverage"] = totalParticipation !== 0 ? totalCoverage / totalParticipation : 0;

            participant["platform-type"] = participant["platform_type_name"];

            return {
                measure: participant.name,
                icon: {
                    url: getParticipantIconUrl(participant),
                    width: 32,
                    height: 32,
                    padding: {
                        left: 0,
                        right: 8
                    },
                    background_class: participant["platform-type"]
                },
                percentage: {
                    measure: participant["percent-coverage"] + " %",
                    class: "ypercentage_" + calculatePercentageClass(participant["percent-coverage"])
                },
                data: periods
            }
        });
        serial.participants = currSerialParticipants;
        serial["overall_average"] = participants.length
            ? (
                participants
                  .map(p => p["percent-coverage"])
                  .reduce((s, d) => s + d, 0)
                / participants.length
            )
            : 0;
        serial.includeInTimeline = true;  // this should come from the database
        return serial;
    })
    return transformedData;
}

function renderCharts(serials) {
    const transformedSerials = transformSerials(serials);

    if (!generatedCharts) {
        console.log('Generating charts.');
        for (i = 0; i < serials.length; i++) {
            console.log(serials[i].serial, serials[i].overall_average);

            if (!serials[i].includeInTimeline) {
                console.log("Serial flag 'includeInTimeline' false, won't generate chart.");
                continue;
            }

            // take deep copy of data. For some reason using a dataset
            // more than once mangles it
            const data = JSON.parse(JSON.stringify(transformedSerials[i]));

            chartOptions.push({...defaultOptions});
            addChartDiv(i + 1, serials[i].serial, "" + calculatePercentageClass(serials[i].overall_average));
            // override the target ids
            chartOptions[i].id_div_container = "visavail_container_new_" + (i + 1);
            chartOptions[i].id_div_graph = "visavail_graph_new_" + (i + 1);

            // create new chart instance
            charts[i] = visavail.generate(chartOptions[i], data);
        }
        generatedCharts = true;

    } else {
        console.log('Charts already generated, updating charts.');
        for (i = 0; i < serials.length; i++) {
            console.log(serials[i].serial, serials[i].overall_average);
            if (!serials[i].includeInTimeline) {
                console.log("Serial flag 'includeInTimeline' false, won't update chart.");
                continue;
            }
            const data = JSON.parse(JSON.stringify(transformedSerials[i]));
            charts[i].updateGraph(chartOptions[i], data);
        }
    }
}

function renderTimelines() {
    const transformedSerials = transformSerials2();
    console.log('transformedSerials2', transformedSerials);

    if (!generatedCharts) {
        console.log('Generating charts.');
        for (i = 0; i < transformedSerials.length; i++) {
            console.log(transformedSerials[i].name, transformedSerials[i].overall_average);

            if (!transformedSerials[i].includeInTimeline) {
                console.log("Serial flag 'includeInTimeline' false, won't generate chart.");
                continue;
            }

            // take deep copy of data. For some reason using a dataset
            // more than once mangles it
            const data = JSON.parse(JSON.stringify(transformedSerials[i]));

            chartOptions.push({...defaultOptions});
            addChartDiv(
                i + 1,
                transformedSerials[i].name,
                "" + calculatePercentageClass(transformedSerials[i].overall_average)
            );
            // override the target ids
            chartOptions[i].id_div_container = "visavail_container_new_" + (i + 1);
            chartOptions[i].id_div_graph = "visavail_graph_new_" + (i + 1);

            // create new chart instance
            charts[i] = visavail.generate(chartOptions[i], transformedSerials[i].participants);
        }
        generatedCharts = true;

    } else {
        console.log('Charts already generated, updating charts.');
        for (i = 0; i < serials.length; i++) {
            console.log(transformedSerials[i].name, transformedSerials[i].overall_average);
            if (!transformedSerials[i].includeInTimeline) {
                console.log("Serial flag 'includeInTimeline' false, won't update chart.");
                continue;
            }
            charts[i].updateGraph(chartOptions[i], transformedSerials[i].participants);
        }
    }
}



window.onload = (event) => {
  fetchConfig();
};
