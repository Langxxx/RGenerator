# RGenerator
Gore is a tool to generate each router info for swift enum case

## Demo
for swift enum

```swift
enum Demo {
	//@pattern /profile/channel/:id
    case channelDetail(id: String)
    //@pattern
    case search
    /@pattern /profile/member
    case memberProfile(id: String)
    //@pattern
    case emailOrPhone(isEmail: Bool)
}
```

code was generated after build

```swift
public extension Demo {
    public var path: String {
        switch self {
        case let .channelDetail(id): return "/profile/channel/\(id)"
        case .search: return "/search"
        case .memberProfile: return "/profile/member"
        case .emailOrPhone: return "/email_or_phone"
        }
     }

     public var parameter: [String : Any]? {
        switch self {
        case let .channelDetail(id):
            var p: [String: Any] = [:]
            p["id"] = id
            return p
        case let .memberProfile(id):
            var p: [String: Any] = [:]
            p["id"] = id
            return p
		...
        }
     }
}

public extension Demo {
    public struct ChanneldetailCaseInfo {
        public static let parttern = "/profile/channel/:id"
        struct Parameter {
            static let id = "id"
        }
    }
    public struct SearchCaseInfo {
        public static let parttern = "/search"
        struct Parameter {
        }
    }
	...
}
```

## Usage
1. Add `pod 'RGenerator'` to your [Podfile](http://cocoapods.org/#get_started) and run `pod install`
2. In Xcode: Click on your project in the file list, choose your target under `TARGETS`, click the `Build Phases` tab and add a `New Run Script Phase` by clicking the little plus icon in the top left
3. Drag the new `Run Script` phase **above** the `Compile Sources` phase and **below** `Check Pods Manifest.lock`, expand it and paste the following script:
  
   ```
   "$PODS_ROOT/RGenerator/generate" -i "YOUR/ENUM/FILE"
   ```
   
4. Build your project, in Finder you will now see a `Router.Generate.swift` in the folder same with input file path, drag the `Router.Generate.swift` files into your project

*Suggestion:* Add the `Router.Generate.swift ` pattern to your `.gitignore` file to prevent unnecessary conflicts.

