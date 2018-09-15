let form = document.getElementById("order");
            form.onsubmit = function() {

                if (!form.airport.value)
                {
                    alert("missing airport");
                    return false;
                }
                else if (!form.date.value)
                {
                    alert("missing date");
                    return false;
                }
                else if (!form.otime.value)
                {
                    alert("missing optimal time");
                    return false;
                }
                else if (!form.number.value)
                {
                    alert("missing number in party");
                    return false;
                }
                else if (!form.etime.value)
                {
                    alert("missing etime");
                    return false;
                }

            };
