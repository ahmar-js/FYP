// ============= Form validation 

// Example starter JavaScript for disabling form submissions if there are invalid fields
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

// ============= Form validation end

// ============= Alert box


        // Function to show the Bootstrap 5 alert with the dropped column name and hide it after a specified duration
        // function showDropAlert(columnName) {
        //     var alertHtml = `
        //         <div class="alert alert-success alert-dismissible fade show" role="alert">
        //             Column <strong>'${columnName}'</strong> has been dropped!
        //             <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        //         </div>
        //     `;
    
        //     // Append the alert to the 'alert-container' div
        //     document.getElementById('alert-container').innerHTML = alertHtml;
    
        //     // Set a timer to hide the alert after 3 seconds (3000 milliseconds)
        //     setTimeout(function () {
        //         var alertElement = document.querySelector('.alert');
        //         if (alertElement) {
        //             alertElement.remove();
        //         }
        //     }, 3000); // 3000 milliseconds = 3 seconds
        // }

// ============= alert box end


// ============= Fill constant value 


    // Function to enable or disable the "Fill Constant" input field based on the selected radio button
    function handleConstantInput() {
        var strategyInput = document.getElementById('strategy_input');
        var strategyConstant = document.getElementById('strategy_constant');

        if (strategyInput.checked) {
            strategyConstant.removeAttribute('disabled');
        } else {
            strategyConstant.setAttribute('disabled', 'disabled');
        }
    }

    // Attach the handleConstantInput function to the onchange event of the radio inputs
    var radioInputs = document.querySelectorAll('input[type="radio"][name="strategy"]');
    radioInputs.forEach(input => {
        input.addEventListener('change', handleConstantInput);
    });

// ============= Fill constant value end





//============= function to handle the coordinae systems and units

    function updateDataUnitOptions() {
        const gcsRadio = document.getElementById('cord-sys-gcs');
        const pcsRadio = document.getElementById('cord-sys-pcs');
        const dgRadio = document.getElementById('cord-sys-unit-dg');
        const mtRadio = document.getElementById('cord-sys-unit-mt');
        const ftRadio = document.getElementById('cord-sys-units-ft');
        const kmRadio = document.getElementById('cord-sys-unit-km');

        if (gcsRadio.checked) {
            // If GCS radio button is checked, enable Decimal Degrees and disable the other data units
            dgRadio.disabled = false;
            mtRadio.disabled = true;
            ftRadio.disabled = true;
            kmRadio.disabled = true;
        } else if (pcsRadio.checked) {
            // If PCS radio button is checked, enable Meters, Feet, and Kilometers and disable Decimal Degrees
            dgRadio.disabled = true;
            mtRadio.disabled = false;
            ftRadio.disabled = false;
            kmRadio.disabled = false;
        }
    }

//============= function to handle the coordinae systems and units end

//============= function to handle star parameter option

function updateStarParameterOptions() {
    var selectStarParameterCheckbox = document.getElementById('select_star_parameter');
    var starParameterInput = document.getElementById('star_parameter');

    // Enable/disable the star_parameter input based on checkbox state
    if (selectStarParameterCheckbox.checked) {
        starParameterInput.removeAttribute('disabled');
        starParameterInput.setAttribute('required', 'true');
    } else {
        starParameterInput.setAttribute('disabled', 'true');
        starParameterInput.removeAttribute('required');
    }
}

// Attach the onchange event handler to the checkbox
document.getElementById('select_star_parameter').onchange = updateStarParameterOptions;

//============= function to handle star parameter option end

//============= function to handle view report button

// document.addEventListener('DOMContentLoaded', function() {
//     // Check if the form has been submitted recently (you can use a hidden input field to track this)
//     var formSubmitted = localStorage.getItem('formSubmitted');
    
//     // Get the "View report" button element
//     var viewReportButton = document.getElementById('view_hotspot_report');
    
//     // Check if the form has been submitted and enable the button if necessary
//     if (formSubmitted === 'true') {
//         viewReportButton.removeAttribute('disabled');
//     }
    
//     // Add an event listener to the form submission
//     document.querySelector('form-hotspot').addEventListener('submit', function() {
//         // Set a flag in local storage to indicate that the form has been submitted
//         localStorage.setItem('formSubmitted', 'true');
//     });
// });

//============= function to handle view report button end


// ============ ajax for data limiter

// document.addEventListener("DOMContentLoaded", function () {
//     const form = document.querySelector("#previewdata-limit");
//     const tableBody = document.querySelector(".preview-table tbody");
//     const recordInfo = document.querySelector(".preview-record-info"); // Reference to the record info element

//     form.addEventListener("submit", function (event) {
//         event.preventDefault();
//         const dataLimit = form.querySelector("#datalimit").value;
//         const ajaxUrl = form.getAttribute("data-ajax-url");
//         const url = `${ajaxUrl}?datalimit=${dataLimit}`;

//         fetch(url)
//             .then(response => response.json())
//             .then(data => {
//                 console.log(data)
//                 tableBody.innerHTML = "";  // Clear existing table rows
//                 data.data.forEach(row => {
//                     const newRow = document.createElement("tr");
//                     row.forEach(value => {
//                         const newCell = document.createElement("td");
//                         // Handle null values by replacing them with a placeholder
//                         const displayValue = value === null ? "N/A" : value;
//                         newCell.textContent = displayValue;
//                         newRow.appendChild(newCell);
//                     });
//                     tableBody.appendChild(newRow);
//                 });
            

//                 // Update the record info element with the number of records being shown
//                 const numRecordsShown = data.data.length;
//                 const recordsText = numRecordsShown === 1 ? "record" : "records";
//                 recordInfo.textContent = `Showing ${numRecordsShown} ${recordsText}`;
//             })
//             .catch(error => console.error("Error fetching data:", error));
//     });
// });


// $(document).ready(function () {
//     $('#previewdata-limit').submit(function (event) {
//         event.preventDefault(); // Prevent default form submission
//         var selectedLimit = $('#datalimit').val();

//         $.ajax({
//             url: '/preview_data/', // Update with your actual URL
//             type: 'GET',
//             data: { limit: 10 }, // Pass the selected limit as a parameter
//             success: function (data) {
//                 console.log('AJAX request succeeded:', data);
//                 $('#preview-data-container').html(data.html); // Update the container with fetched data
//             },
//             error: function (error) {
//                 console.log('Error fetching data: ' + error);
//             }
//         });
//     });
// });

$(document).ready(function () {
    function loadData(limit) {
        $.ajax({
            url: '/preview_data/',
            type: 'GET',
            data: { limit: limit },
            success: function (data) {
                // console.log('AJAX request succeeded:');
                // console.log('AJAX request succeeded:', data);
                // Parse the JSON data received from the server
                var jsonData = JSON.parse(data.data);
                // Check if the data is empty
                if (jsonData.length === 0) {
                    $('#preview-data-container').html('<p class="text-info"><b>Nothing to show.<b></p><br><p>Redirecting in 5 seconds...</p>');
                    // Set a timeout to redirect after 5 seconds
                    setTimeout(function () {
                        window.location.href = '/upload/'; // Replace with your desired URL
                    }, 5000); // 5000 milliseconds (5 seconds)
                    return; // Exit the function early
                }
                
                // console.log('jsonData:', jsonData);

                // console.log('JSON data received:', jsonData)

                // Create and populate the table with the JSON data
                var tableHtml = '<table class = "table table-bordered table-dark table-hover">';
                tableHtml += '<thead><tr>';
                for (var key in jsonData[0]) {
                    tableHtml += '<th>' + key + '</th>';
                }
                tableHtml += '</tr></thead>';

                tableHtml += '<tbody>';
                for (var i = 0; i < jsonData.length; i++) {
                    tableHtml += '<tr>';
                    for (var key in jsonData[i]) {
                        tableHtml += '<td>' + jsonData[i][key] + '</td>';
                    }
                    tableHtml += '</tr>';
                }
                tableHtml += '</tbody>';
                tableHtml += '</table>';

                // Update the container with the table
                // console.log(tableHtml);
                $('#preview-data-container').html(tableHtml);
            },
            error: function (error) {
                console.log('Error fetching data:', error);
            }
        });
    }

    // Load default data on page load
    loadData(10); // Load default 10 rows
    updateStatistics()

    // Handle form submission
    $('#previewdata-limit').submit(function (event) {
        event.preventDefault();
        var selectedLimit = $('#datalimit').val();
        loadData(selectedLimit);

        // Update selected record info
        $('#selected-record-info').text('Showing ' + selectedLimit + ' records');
    });

    // Handle "Drop Column" form submission
    $('#dropcolumn-form').submit(function (event) {
        event.preventDefault();
        var selectedColumn = $('#dropcolumnmenu').val();
        // Perform AJAX request to handle column drop
        // Update the DataFrame in the session, and update statistics
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        $.ajax({
            headers: {'X-CSRFToken': csrftoken},
            url: '/handle_drop_columns/',
            type: 'POST',
            data: { column: selectedColumn },
            success: function (response) {
                showAlert('success', response.message, '#dropcolumn-alert-container');
                var selectedLimit = $('#datalimit').val();
                // console.log("here");
                // Update the DataFrame in the session
                response.data_frame;
                // Refresh data
                loadData(selectedLimit);
                updateStatistics()
                // Remove the dropped column from the dropdown menu
                $('#dropcolumnmenu option[value="' + selectedColumn + '"]').remove();
                $('#fillnullvalues option[value="' + selectedColumn + '"]').remove();
                $('#select-col-convert-dtype option[value="' + selectedColumn + '"]').remove();

                $('#select-multi-drop-row').selectpicker('deselectAll'); // Deselect all options
                $('#select-multi-drop-row').selectpicker('val', ''); // Clear the selected values
                // Remove the dropped column from the Bootstrap Selectpicker
                $('#select-multi-drop-row option[value="' + selectedColumn + '"]').remove();
                $('#select-multi-drop-row').selectpicker('refresh'); // Refresh the Selectpicker
                
                
            },
            error: function (error) {
                console.log('Error handling drop column:', error);
            }
        });
    });
    
    // Handle "Fill Null Values" form submission
    $('#fill_na_values').submit(function (event) {
        event.preventDefault();
        var selectedColumn = $('#fillnullvalues').val();
        var selectedStrategy = $('input[name="strategy"]:checked').val();
        if (selectedStrategy == 'input_constant'){
            var constantValue = $('input[name="strategy_constant"').val();
        }
        // Perform client-side validation to check the data type
        else if ((selectedStrategy === 'mean' || selectedStrategy === 'median') && !isNumericColumn(selectedColumn)) {
            showAlert('danger', '<b>Mean</b> or <b>Median</b> strategies can only be applied to numeric columns.', '#fillna-alert-container');
            return;
        }
        // console.log(selectedStrategy);
        // console.log(constantValue);
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        $.ajax({
            headers: { 'X-CSRFToken': csrftoken },
            url: '/handle_fill_null_values/',
            type: 'POST',
            data: {
                column: selectedColumn,
                strategy: selectedStrategy,
                constant_value: constantValue
            },
            success: function (response) {
                // console.log(response)
                showAlert('success', response.message, '#fillna-alert-container');
                var selectedLimit = $('#datalimit').val();
                loadData(selectedLimit);
                updateStatistics();
            },
            error: function (error) {
                console.log('Error handling fill null values:', error);
            }
        });

        // Function to check if a column is numeric (int or float)
        function isNumericColumn(columnName) {
            // Retrieve the DataFrame data types from a global variable or AJAX call
            var dataTypes = {}; // Replace with actual data types
            return dataTypes[columnName] === 'int64' || dataTypes[columnName] === 'float64';
        }
    });
    
    // Handle "Drop Rows" form submission
    $('#drop_null_rows').submit(function (event) {
        event.preventDefault();

        // Get selected columns and strategy
        var selectedColumns = $('#select-multi-drop-row').val();
        var selectedStrategy = $('input[name="row_drop_strategy"]:checked').val();

        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        $.ajax({
            headers: { 'X-CSRFToken': csrftoken },
            url: '/handle_drop_rows/',
            type: 'POST',
            data: {
                'select-multi-drop-row': selectedColumns,  // Use the correct key here
                row_drop_strategy: selectedStrategy,
                
            },
            success: function (response) {
                console.log(response);
                showAlert('success', response.message, '#dropnullrows-alert-container');

                var selectedLimit = $('#datalimit').val();
                loadData(selectedLimit);
                updateStatistics();
            },
            error: function (error) {
                console.log('Error handling drop rows:', error);
            }
        });
    });

    // Hide the loading spinner initially
    // hideLoadingSpinner();
    // Function to reload the page and show the spinner
    function reloadPageWithSpinner(response) {
        // Show the loading spinner before reloading the page
        showLoadingSpinner('#loading-spinner-preview-gdf');
        window.location.reload();
        showAlert('success', response.message, '#geodataframe-alert-container');

    }
    // Handle GeoDataFrame conversion form submission
    $('#geodata-conversion-form').submit(function (event) {
        event.preventDefault();

        // Show the loading spinner when the request starts
        // showLoadingSpinner();
        showLoadingSpinner('#loading-spinner-preview-gdf');
        
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const selectedX = $('#select-x').val();
        const selectedY = $('#select-y').val();
        // console.log(selectedX, selectedY);
        if ((selectedX == null || selectedY == null) || (selectedX === selectedY)){
            showAlert('warning', `Please select valid columns.<br> Selected columns <b> ${selectedX}</b> and <b>${selectedY}</b>.`, '#geodataframe-alert-container');
            return;
        }

        $.ajax({
            headers: { 'X-CSRFToken': csrftoken },
            url: '/convert_to_geodataframe/',
            type: 'POST',
            data: {
                'select-x': selectedX,
                'select-y': selectedY,
            },
            success: function (response) {
                // Hide the loading spinner when the request is successful
                hideLoadingSpinner('#loading-spinner-preview-gdf');
                
                // Handle the response, e.g., show a success message
                // console.log(response);

                // Check if the response contains the GeoDataFrame
                // Check if the response contains the GeoDataFrame and its columns
                if (response.geodataframe && response.columns) {
                    // Display the GeoDataFrame in the specified container
                    $('#geodataframe-container').html(response.geodataframe);

                    // Populate the select menus with the new column names
                    populateSelectMenus(response.columns);
            
                    // Show success message
                    reloadPageWithSpinner(response);
                    $('#Loading').removeClass('d-none');
                    $('#preview_dataframe_title').addClass('d-none');

                }
                else if (response.error) {
                    // Show error message
                    showAlert('danger', response.error, '#geodataframe-alert-container');
                } else {
                    showAlert('danger', 'An error occurred during conversion.', '#geodataframe-alert-container');
                }
            },
            error: function (error) {
                hideLoadingSpinner('#loading-spinner-preview-gdf');
                console.log('Error converting to GeoDataFrame:', error);
                // Show error message
                showAlert('danger', `An error occurred during conversion. `, '#geodataframe-alert-container');
            }
        });

    });

    // Handle Getis-Ord Gi* Hotspot Analysis form submission
    $('#gistar-form').submit(function (event) {
        event.preventDefault();

        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const selectedKVal = $('#choose-opt-k').val();
        const selectedGIFeature = $('#select_gi_feature').val();
        const selectStarParameter = $('#select_star_parameter').is(':checked');
        const starParameter = selectStarParameter ? $('#star_parameter').val() : null;

        $.ajax({
            headers: { 'X-CSRFToken': csrftoken },
            url: '/getis_ord_gi_hotspot_analysis/',
            type: 'POST',
            data: {
                K_val: selectedKVal,
                select_gi_feature: selectedGIFeature,
                select_star_parameter: selectStarParameter,
                star_parameter: starParameter,
            },
            success: function (response) {
                // Handle the response, e.g., display results
                console.log(response.json_response);
                var uniqueBins = JSON.parse(response.json_response.unique_bins);
                // Sort the uniqueBins array in ascending order
                uniqueBins.sort(function(a, b) {
                    return a - b;
                });
                var unique_significance_levels = JSON.parse(response.json_response.unique_hotspots);
                console.log('auniqueBins',  unique_significance_levels)

                // Parse the JSON response
                // var graphData = JSON.parse(response.json_response.graph);
                // console.log('graphData', graphData);


                // if (window.Plotly) {
                //     // Plotly is defined, you can use it here
                //     Plotly.plot('graph-container', graphData.data, graphData.layout, graphData.frames);
                // } else {
                //     console.error('Plotly library is not loaded.');
                // }

                // Plotly.react('graph-container', graphData);

                // Check if the response contains the analysis results
                if (response.json_response) {
                    // Get the span element by its ID
                    var spanElement = document.getElementById('extra_stats_unique_bins');

                    // Set the text content of the span element
                    spanElement.textContent = uniqueBins.join(', '); // Join array elements with a comma and space
                    
                    $('#gi-star-reportbody').html(response.json_response.analysis_results);
                    $('#geodataframe-container').html(response.json_response.geodataframe);
                    $('#stats').html(response.json_response.stats);
                    $("#graph-container").html('<img class="img-fluid" src="data:image/png;base64,' + response.json_response.sangi + '" alt="Moran\'s Scatterplot">');
                    // $('#extra_stats_unique_bins').html(uniqueBins);
                    // $('#extra_stats_unique_significance_levels').text(unique_significance_levels);
                    showAlert('success', response.message, '#gistar-alert-container');

                }

                // Enable the "View report", "visualize_hotspot" button
                $('#view_hotspot_report').prop('disabled', false);
                $('#visualize_hotspot').prop('disabled', false);

            },
            error: function (error) {
                console.log('Error performing Getis-Ord Gi* Hotspot Analysis:', error);
            }
        });
    });



    // Function to populate select menus with column names
    function populateSelectMenus(columns) {
        // Clear existing options
        $('#select-x, #select-y').empty();

        // Add a default disabled option
        $('#select-x').append('<option selected disabled value="">Select Long</option>');
        $('#select-y').append('<option selected disabled value="">Select Lat</option>');

        // Add columns as options
        columns.forEach(function (column) {
            $('#select-x').append('<option value="' + column + '">' + column + '</option>');
            $('#select-y').append('<option value="' + column + '">' + column + '</option>');
        });
    }


    // Function to show the loading spinner
    function showLoadingSpinner(id) {
        $(id).removeClass('d-none');
        $(id).addClass('d-inline-block');
        
    }

    // Function to hide the loading spinner
    function hideLoadingSpinner(id) {
        $(id).addClass('d-none');
        $(id).removeClass('d-inline-block');

    }

    function updateStatistics() {
        $.ajax({
            url: '/update_statistics/',  
            type: 'GET',
            success: function (data) {
                // Parse the JSON data received from the server
                var stats = data.stats;
                var describe_data = data.describe_data;
                var unique_dtypes = data.unique_dtypes;
                var null_colwise = data.null_colwise;
                var nonull_colwise = data.nonull_colwise;
                var datatypes = data.datatypes;
    
                // Update the statistics on the page
                $('#num-rows').text(stats.num_rows);
                $('#num-cols').text(stats.num_cols);
                $('#tot_null').text(stats.total_nulls);
                $('#total_notnulls').text(stats.total_notnull);
                $('#describe-data-container').html(describe_data);
                $('#unique-vals-cols').html(unique_dtypes);
                $('#nullwise').html(null_colwise);
                $('#nonullwise').html(nonull_colwise);
                $('#datatypes-table').html(datatypes)

                // Update other statistics elements similarly...
            },
            error: function (error) {
                console.log('Error updating statistics:', error);
            }
        });
    }
    // Function to display alert messages
    function showAlert(type, message, id) {
        // console.log(message);
        var alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        $(id).html(alertHtml);
    }


});



    // // Handle "Fill Null Values" form submission
    // $('#fillnullvalues-form').submit(function (event) {
    //     event.preventDefault();
    //     var selectedColumn = $('#fillnullvalues').val();
    //     var selectedStrategy = $('input[name="strategy"]:checked').val();
    //     var strategyConstant = $('#strategy_constant').val();
    //     // Perform AJAX request to handle null value filling
    //     // Update the DataFrame in the session, and update statistics
    //     // Refresh data if needed
    // });