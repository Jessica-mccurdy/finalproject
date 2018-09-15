let form = document.getElementById("complete");
            form.onsubmit = function() {

                if (!form.rideid.value)
                {
                    alert("please choose a ride");
                    return false;
                }
                else
                {
                    alert("your ride has been marked complete")
                    return true;
                }
            };
