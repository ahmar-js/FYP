(function () {
    'use strict'
    
    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.querySelectorAll('.needs-validation')
    
    // Loop over them and prevent submission
    Array.prototype.slice.call(forms)
    .forEach(function (form) {
      form.addEventListener('submit', function (event) {
        if (!form.checkValidity()) {
          event.preventDefault()
          event.stopPropagation()
        }
    
        form.classList.add('was-validated')
      }, false)
    })
    })()


// intensity map

// $(document).ready(function () {
//     $('#select_map').change(function () {
//         var selected_dataset_id = $('#selectDataset').val();
//         var select_map = $(this).val();
//         var geodata_check = false;
    
//             $.ajax({
//                 type: "GET",
//                 url: "/retrieve_column_names_df/", 
//                 data: {
//                     selected_dataset_id: selected_dataset_id,
//                     // selected_geo_id: selected_geo_id,
//                     select_map: select_map,
//                     geodata_check: geodata_check,
//                 },
//                 success: function (data) {
//                     if (data.message === "Success") {
//                         console.log(data)
//                         $("#mapbox-container").html(data.json_response.map);
                        
    
//                     }
//                 },
//                 error: function (jqXHR, textStatus, error){
//                     alert(error)
//                 }
                
//             });
//         });


//     });

// for fb and arima

$(document).ready(function () {
    $("#selectForecasts").change(function () {
        var selectedDatasetId = $('#selectDataset').val();
        var selectedPresult = $(this).val();
        var selected_model = $('#selectModel').val();
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        if (selected_model === 'fbprophet'){
            urll = '/get_prophet_results/'
        }
        else{
            urll = '/get_arima_results/'
        }

        $.ajax({
            headers: { 'X-CSRFToken': csrftoken },
            url: urll,
            type: 'POST',
            data: {
                selectedDatasetId: selectedDatasetId,
                selectedPresult: selectedPresult,

            },
            success: function (data) {
                if (data.message === "Success") {
                    console.log(data)
                    if (data.json_response_fb){
                        var fbplot = JSON.parse(data.json_response_fb.fb_plot);

                        Plotly.newPlot('fbplot_arimaplot', fbplot);
                        $('#predicted_label').html(data.json_response_fb.predictions);
                    }
                    else{
                        console.log(data)
                        var arimaplot = JSON.parse(data.json_response_arima.arimaplot);
                        Plotly.newPlot('fbplot_arimaplot', arimaplot);
                        $('#predicted_label').html(data.json_response_arima.predictions);

                        

                    }

                }
            },
            error: function (jqXHR, textStatus, error){
                alert(error)
            }

        });
        
    });
});

// // plot folium datapoints

// $(document).ready(function () {
//     function updateMap() {
//         var selected_dataset_id = $("#selectDataset").val();
//         var selected_geo_id = $('#Select_geodataframe').val();
//         var select_map = $('#select_map').val();
//         var geodata_check = false;

//         $.ajax({
//             type: "GET",
//             url: "/retrieve_column_names_df/", 
//             data: {
//                 selected_dataset_id: selected_dataset_id,
//                 selected_geo_id: selected_geo_id,
//                 geodata_check: geodata_check,
//                 select_map: select_map,
//             },
//             dataType: "json",
//             success: function (data) {
//                 if (data.message === "success") {
//                     console.log(data);
//                     // Inject the map HTML into the map-container div.
//                     if (select_map === 'intensity'){
//                         $("#mapbox-container").html(data.json_response.imap);
//                     }
//                     else{
//                         $("#mapbox-container").html(data.json_response.dmap);
//                     }
//                 } else {
//                     alert("Error: " + data.error);
//                 }
//             },
//             error: function () {
//                 alert("An error occurred while fetching the map.");
//             },
//         });
//     }
//     // Listen for changes in the dataset selection
//     $("#selectDataset").change(updateMap);
//     // Listen for changes in the geo column selection
//     $('#select_map').change(updateMap);

//     // Call updateMap initially to load the initial map
//     // updateMap();
// });


// plotting plotly 3d scatter plot and chloropeths
$(document).ready(function () {
        // function updateMaphp() {
        $('#dashboard_sidenav_form').submit(function (event) {
        event.preventDefault();

        console.log("here")
        // Get the selected_dataset_id, selected_geo_id, and geodata_check from your form or wherever they are available.
        var selected_geo_idd = $('#Select_geodataframe').val();
        var selected_dataset_idd = $('#selectDataset').val()
        var select_map = $('#select_map').val();
        // var selected_geo_id = $('#Select_geodataframe').val();
        // var geodata_checkk = true;
        var select_hp_timely_mode = $('#select_hp_timely_mode').val();

        $.ajax({
            type: "GET",
            url: "/retrieve_column_names/", 
            data: {
                selected_dataset_idd: selected_dataset_idd,
                selected_geo_idd: selected_geo_idd,
                select_map: select_map,
                // geodata_checkk: geodata_checkk,
                select_hp_timely_mode: select_hp_timely_mode,
            },
            dataType: "json",
            success: function (data) {
                if (data.message === "success") {
                    console.log(data);
                    if (select_hp_timely_mode == 'scatter'){
                        var bubble = JSON.parse(data.json_response_geo.plotly_chloro_fig_scatter);
                        Plotly.newPlot('plotly_chloropeth', bubble);
                    }
                    else{
                        var chloro = JSON.parse(data.json_response_geo.plotly_chloro_fig_chloro);
                        Plotly.newPlot('plotly_chloropeth', chloro);
                    }
                    var hot3d = JSON.parse(data.json_response_geo.fig);
                    Plotly.newPlot('hotspot_growth_chart', hot3d);

                    if (select_map === 'intensity'){
                            $("#mapbox-container").html(data.json_response_folium.imap);
                        }
                    else{
                        $("#mapbox-container").html(data.json_response_folium.dmap);
                    }
                    
                    // Inject the map HTML into the map-container div.
                    // $("#mapbox-container").html(data.json_response.map);
                } else {
                    alert("Error: " + data.error);
                }
            },
            error: function () {
                alert("An error occurred while fetching the map.");
            },
        });
// }
    });
// $("#selectDataset").change(updateMaphp);
// $('#select_map').change(updateMaphp);
// $("#Select_geodataframe").change(updateMaphp);
// $("#select_hp_timely_mode").change(updateMaphp);
});



$(document).ready(function () {
    // Event listener for changes in the dataset selection dropdown
    $('#selectDataset').change(function () {
        var selectedDatasetId = $(this).val();
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Make an AJAX request to fetch the selected dataset's model results
        $.ajax({
            headers: { 'X-CSRFToken': csrftoken },
            url: '/get_model_results/',
            type: 'POST',
            data: {
                selectedDatasetId: selectedDatasetId

            },
            success: function (response) {
                console.log(response);
                populatenumericSelectMenus(response.json_response.numeric_columns);
                populatenonnumericSelectMenus(response.json_response.df_columns);
                
                //header stats
                $('#confirmed_label').html(response.json_response.df_rows);

                //cases table
                $('#cases_table_container').html(response.json_response.dataframe);
                $('#total_hotspot_label').html(response.json_response.total_hs_rec);

                $('#total_pred_label').html(response.json_response.total_rec);

                // Enable the "selectModel" dropdown
                $('#selectModel').prop('disabled', false);

                // Clear and enable the "selectForecasts" and select_geodataframe dropdown
                var selectForecasts = $('#selectForecasts');
                selectForecasts.empty().prop('disabled', false);
                var select_geodataframe = $('#Select_geodataframe');     
                select_geodataframe.empty().prop('disabled', false)           

                // Populate the "selectForecasts" dropdown based on the selected model
                $('#selectForecasts').empty();
                var selectedModel = $('#selectModel').val();

                // Update the forecasts dropdown when the model selection changes
                $('#selectModel').change(function () {
                    var selectedModel = $(this).val();
                    $('#selectForecasts').empty();


                    selectForecasts.append('<option selected disabled value="">Select File</option>');
                    for (var i = 0; i < response.json_response.modelResults.length; i++) {
                        var result = response.json_response.modelResults[i];
                        if ((selectedModel == 'fbprophet' && result.model == 'fbprophet') || (selectedModel == 'arima' && result.model == 'arima')) {
                            selectForecasts.append($('<option>', {
                                value: result.id,
                                text: result.file + ' --- ' + result.updated_at
                            }));
                        }
                    }
                    

                    
                });

                select_geodataframe.append('<option selected disabled value="">Select File</option>');

                for (var i = 0; i < response.json_response.gdf_results.length; i++) {
                    var geo_result = response.json_response.gdf_results[i];
                    select_geodataframe.append($('<option>', {
                            value: geo_result.id,
                            text: geo_result.file + ' --- ' + geo_result.updated_at
                        }));
                }
 

                // Call the change event once to initialize the forecasts dropdown
                $('#selectModel').change();
            },
            error: function (error) {
                console.log('Error fetching model results:', error);
            }


        });
    });



    
    // Function to populate select menus with column names
    function populatenumericSelectMenus(columns) {
        // Clear existing options
        $('#conf_select_x, #conf_select_y, #select_size').empty();

        // Add a default disabled option
        $('#conf_select_x').append('<option selected disabled value="">Select Long</option>');
        $('#conf_select_y').append('<option selected disabled value="">Select Lat</option>');
        $('#select_size').append('<option selected disabled value="">Select size</option>');

        // Add columns as options
        columns.forEach(function (column) {
            $('#conf_select_x').append('<option value="' + column + '">' + column + '</option>');
            $('#conf_select_y').append('<option value="' + column + '">' + column + '</option>');
            $('#select_size').append('<option value="' + column + '">' + column + '</option>');
        });
    }
    function populatenonnumericSelectMenus(columns) {
        // Clear existing options
        $('#select_filtered_col, #select_color_col, #select_location_col, #select_hover_data_col, #select_date').empty()
        // Add a default disabled option
        $('#select_filtered_col').append('<option selected disabled value="">Select filter column</option>');
        $('#select_color_col').append('<option selected disabled value="">Select categorical</option>');
        $('#select_location_col').append('<option selected disabled value="">Select location attribute</option>');
        $('#select_hover_data_col').append('<option selected disabled value="">Select feature to hover</option>');
        $('#select_date').append('<option selected disabled value="">Select date</option>');


        // Add columns as options
        columns.forEach(function (column) {
            $('#select_filtered_col').append('<option value="' + column + '">' + column + '</option>');
            $('#select_color_col').append('<option value="' + column + '">' + column + '</option>');
            $('#select_location_col').append('<option value="' + column + '">' + column + '</option>');
            $('#select_hover_data_col').append('<option value="' + column + '">' + column + '</option>');
            $('#select_date').append('<option value="' + column + '">' + column + '</option>');
        });
    }

    $('#Select_geodataframe').change(function () {
        var Select_geodataframe = $('#Select_geodataframe').val();
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Make an AJAX request to fetch the selected dataset's model results
        $.ajax({
            headers: { 'X-CSRFToken': csrftoken },
            url: '/Geodatafileselection/',
            type: 'POST',
            data: {
                Select_geodataframe: Select_geodataframe

            },
            success: function (response) {
                console.log(response);
                populatenumericSelectMenus(response.json_response.numeric_columns);
                populatenonnumericSelectMenus(response.json_response.gdf_columns);

                $('#confirmed_label').html(response.json_response.gdf_rows);
                $('#cases_table_container').html(response.json_response.gdataframe);

            },
            error: function (error) {
                console.log('Error fetching model results:', error);
            }


        });

    });


});


