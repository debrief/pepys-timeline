moment.locale("en");

let generatedCharts = false;
let charts = [];
let chartOptions = [];

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

function fetchSerials() {
    console.log('fetching serials');
    fetch('/timelines')
      .then(response => response.json())
      .then(response => {
        const { serials } = response;
        renderCharts(serials);
      })
      .catch(err => console.error(err));
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
                    background_class: participant["platform-type"]
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



window.onload = (event) => {
  fetch('/config')
    .then(response => response.json())
    .then(response => {
        const { frequency_secs } = response;
        fetchSerials();
        setInterval(fetchSerials, frequency_secs * 100);

    })
    .catch(err => console.error(err));

  const serial_participants = [{
    "serial_id": "faa18ef7-6823-33dc-0f16-de6e4b2c02f3",
    "platform_id": "50d64387-9f91-4c6f-8933-f4e7b1a7d8ab",
    "start": "2020-11-15 00:00:00",
    "end": "2020-11-15 23:59:59",
    "gap_seconds": 30
  }];
  const range_types = ["G", "C"];

  let url = new URL(window.location + 'dashboard_stats');
  let queryParams = new URLSearchParams();
  queryParams.set('serial_participants', JSON.stringify(serial_participants));
  queryParams.set('range_types', JSON.stringify(range_types));
  url.search = queryParams.toString();

  fetch(url)
    .then(response => response.json())
    .then(response => {
        console.log('testing dashboard_stats', response);
    })

  url = new URL(window.location + 'dashboard_metadata');
  queryParams = new URLSearchParams();
  queryParams.set('from_date', '2021-01-05');
  queryParams.set('to_date', '2021-01-05');
  url.search = queryParams.toString();

  fetch(url)
    .then(response => response.json())
    .then(response => {
        console.log('testing dashboard_metadata', response);
    })
};
