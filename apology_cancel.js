let form = document.getElementById("cancel");
            form.onsubmit = function() {

                if (!form.rideid.value)
                {
                    alert("please choose a ride");
                    return false;
                }
                else
                {
                    alert("your ride has been cancelled")
                    return true;
                }
            };
