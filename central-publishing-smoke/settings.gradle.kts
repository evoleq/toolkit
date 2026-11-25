// This is a separate consumer: no project(...) and no Maven Local fallback.
pluginManagement {
    repositories {
        gradlePluginPortal()
        google()
        mavenCentral()
    }
}
dependencyResolutionManagement {
    repositories {
        if (!providers.gradleProperty("centralRemote").map { it.toBoolean() }.getOrElse(false)) {
            maven(url = uri("../build/central-staging"))
        }
        google()
        mavenCentral()
    }
}
rootProject.name = "toolkit-central-consumer"
