# Per-repo fleet start config for ednaficator
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'ednaficator'
    BackendPort  = 10942
    FrontendPort = 10943
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\ednaficator\ui'
    Backend = @{
        Kind          = 'uvicorn'
        WorkDir       = 'D:\Dev\repos\ednaficator'
        UvicornTarget = 'api_bridge:app'
        SyncExtras    = @('dev')
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
