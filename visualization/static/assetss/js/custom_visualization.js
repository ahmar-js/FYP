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

    $('#done_hotspot').change(function () {
        var donehotspot = $('#done_hotspot');
        if (donehotspot.is(":checked")) {
            $("#select_color_col").prop('disabled', true); // Enable the element
        } else {
            $("#select_color_col").prop('disabled', false);  // Disable the element
        }
    });


    function populateGeoDataFrame(columns){
        $('#Select_geodataframe').empty();
        $('#Select_geodataframe').append('<option selected disabled value="">Select File</option>');
        columns.forEach(function (column) {
            $('#Select_geodataframe').append('<option value="' + column + '">' + column + '</option>');
        });

    }
    
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
        $('#select_filtered_col').append('<option selected disabled value="">Select Long</option>');
        $('#select_color_col').append('<option selected disabled value="">Select Lat</option>');
        $('#select_location_col').append('<option selected disabled value="">Select size</option>');
        $('#select_hover_data_col').append('<option selected disabled value="">Select size</option>');
        $('#select_date').append('<option selected disabled value="">Select size</option>');


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
            },
            error: function (error) {
                console.log('Error fetching model results:', error);
            }


        });

    });


});

