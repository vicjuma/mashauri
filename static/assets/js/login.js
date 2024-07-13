$(document).ready(function () {
    console.log("Document ready");

    // Ensure no previous event listeners are attached to the form submission
    $('#login_form').off('success.form.bv').on('success.form.bv', function (e) {

        // Prevent form submission
        e.preventDefault();

        // Disable the submit button to prevent multiple submissions
        $('#submit_button').prop('disabled', true);

        // Get the form instance
        var $form = $(e.target);

        // Use Ajax to submit form data
        var formData = new FormData($form[0]);

        $.ajax({
            url: $form.attr('action'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function (result) {
                $('#error_message').hide();
                $('#success_message').slideDown({ opacity: "show" }, "slow");
                $('#login_form').data('bootstrapValidator').resetForm();
                console.log("Form submitted successfully", result);
                setTimeout(() => {
                    $('#success_message').text('Form submitted successfully!').show();
                    $('#submit_button').prop('disabled', false); // Re-enable the button if needed
                }, 3000)
                setTimeout(() => {
                    if (result.role === "ENTERPRISE CONNECTIVITY") {
                        window.location.href = '/dashboard/ec';

                    } else if (result.role === "FDP") {
                        window.location.href = '/dashboard/fdp';
                    } else if (result.role === "MSP") {
                        window.location.href = '/dashboard/msp';
                    } else if (result.role === "ENTERPRISE_PROJECT") {
                        window.location.href = '/dashboard/ep';
                    } else if (result.role === "SUPPORT") {
                        window.location.href = '/dashboard/support';
                    } else if (result.role === "ROLLOUT_PARTNER") {
                        window.location.href = '/dashboard/rp';
                    }
                    console.log(result.role);
                }, 3000)
            },
            error: function (jqXHR, textStatus, errorThrown) {
                $('#error_message').slideDown({ opacity: "show" }, "slow");
                $('#submit_button').prop('disabled', false); // Re-enable the button if needed
            }
        });
    });

    // BootstrapValidator initialization
    $('#login_form').bootstrapValidator({
        feedbackIcons: {
            valid: 'glyphicon glyphicon-ok',
            invalid: 'glyphicon glyphicon-remove',
            validating: 'glyphicon glyphicon-refresh'
        },
        fields: {
            username: {
                validators: {
                    notEmpty: {
                        message: 'Please supply the username'
                    }
                }
            },
            password: {
                validators: {
                    notEmpty: {
                        message: 'Please supply the password'
                    }
                }
            },

        }
    });

    // Ensure the form is not submitted traditionally
    $('#login_form').on('submit', function (e) {
        e.preventDefault();
    });
});
