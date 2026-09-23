// -----------------------------------------------
// Warning for exiting form without saving changes
// -----------------------------------------------

let suppressBeforeUnload = true;
let submitButtons = document.querySelectorAll("button");
let formFields = document.querySelectorAll("input");

let formFieldsInitial = new Map(
    Array.from(formFields).map(field => [field, field.value])
);

window.addEventListener('beforeunload', function (event) {
    if (suppressBeforeUnload) return;

    event.preventDefault();
    event.returnValue = '';
});

// Enable exit warning if any inputs have been changed
formFields.forEach(function (field) {
    field.addEventListener("change", function () {
        suppressBeforeUnload = true;
        for (const field of formFields) {
            if (field.value != formFieldsInitial.get(field)) {
                suppressBeforeUnload = false;
                break;
            }
        }
    });
});

// Supress warning if changes are being saved or moderation applied
submitButtons.forEach(function (button) {
    if (button.id != "return-btn") {
        button.addEventListener("click", function () {
            suppressBeforeUnload = true;
        });
    }
});


// ----------------------------------------------------------
// Reveal grade moderation parameters once algorithm selected
// ----------------------------------------------------------

let algInitial = document.getElementById("grade-moderation-alg").value;

function revealModerationParams(input) {
    const param1 = document.getElementById("param-1");
    const param2 = document.getElementById("param-2");
    const param1Text = document.getElementById("param-1-text");
    const param2Text = document.getElementById("param-2-text");

    if (input.value == algInitial) {
        param1.value = formFieldsInitial.get(param1);
        param2.value = formFieldsInitial.get(param2);
    } else {
        param1.value = null;
        param2.value = null;
    }

    if (input.value == "linear") {
        param1.removeAttribute("hidden");
        param2.removeAttribute("hidden");

        param1Text.innerHTML = "Multiplier: ";
        param1.setAttribute("min", 0);

        param2Text.innerHTML = "Shift: ";
    } else if (input.value == "z-score") {
        param1.removeAttribute("hidden");
        param2.removeAttribute("hidden");

        param1Text.innerHTML = "Target μ: ";
        param1.setAttribute("min", 0);

        param2Text.innerHTML = "Target σ: ";
        param1.setAttribute("min", 0);
    } else {
        param1.setAttribute("hidden", true);
        param2.setAttribute("hidden", true);
        param1.removeAttribute("min");
        param1.removeAttribute("max");
        param2.removeAttribute("min");
        param2.removeAttribute("max");
        param1Text.innerHTML = "";
        param2Text.innerHTML = "";
    }
}


// ----------------------------------------------------------
// Deletion Confirmations
// ----------------------------------------------------------

function confirmCourseDeletion() {
    return confirm('Are you sure you want to delete this course and all of its assignments? \nYou will not be able to undo this action.');
}

function confirmAssignmentDeletion() {
    return confirm('Are you sure you want to delete this assignment and all of its marked submissions? \nYou will not be able to undo this action.');
}

function confirmSubmissionDeletion() {
    return confirm('Are you sure you want to delete this marked submission? \nYou will not be able to undo this action.');
}
