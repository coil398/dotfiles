# Sourced by hook.sh and permission-launcher.sh (POSIX sh).
# When TYPESAFE_API_KEY is absent from the process environment, take it from
# the user service-manager environment that .zshrc publishes to: launchd on
# macOS, the systemd user manager on Linux. Secret files are never read.
case "${TYPESAFE_API_KEY:-}" in
    *[![:space:]]*) ;;
    *)
        jev_service_key=""
        jev_service_source=""
        case "$(uname -s 2>/dev/null)" in
            Darwin)
                jev_service_key=$(launchctl getenv TYPESAFE_API_KEY 2>/dev/null || true)
                jev_service_source=launchd
                ;;
            Linux)
                if command -v systemctl >/dev/null 2>&1; then
                    jev_service_key=$(systemctl --user show-environment 2>/dev/null | sed -n 's/^TYPESAFE_API_KEY=//p' | head -n 1)
                    jev_service_source=systemd
                fi
                ;;
        esac
        case "$jev_service_key" in
            *[![:space:]]*)
                export TYPESAFE_API_KEY="$jev_service_key"
                export JEV_HOOKS_API_KEY_SOURCE="$jev_service_source"
                ;;
        esac
        unset jev_service_key jev_service_source
        ;;
esac
