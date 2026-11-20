#define _GNU_SOURCE

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

#define MODULE_PATH "/var/lib/legion-center/acpi_call.ko"

int main(void)
{
    int module_fd = open(MODULE_PATH, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (module_fd < 0) {
        fprintf(stderr, "Cannot open %s: %s\n", MODULE_PATH, strerror(errno));
        return 1;
    }

#ifdef SYS_finit_module
    int result = (int)syscall(SYS_finit_module, module_fd, "", 0);
#else
    errno = ENOSYS;
    int result = -1;
#endif

    int load_error = errno;
    close(module_fd);

    if (result == 0 || load_error == EEXIST) {
        return 0;
    }

    fprintf(stderr, "Cannot load acpi_call: %s\n", strerror(load_error));
    return 1;
}
