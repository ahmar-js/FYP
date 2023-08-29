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



