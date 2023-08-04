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




