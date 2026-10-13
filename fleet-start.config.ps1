# Per-repo fleet start config for ednaficator
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'ednaficator'
    BackendPort  = 10942
    FrontendPort = 10943
    HealthPath   = '/health'
    WebRoot      = '.'
    Backend = @{
        Kind       = 'module-serve'
        Module     = 'ednaficator'
        SyncExtras = @('dev')
        SyncOnStart  = $true
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
