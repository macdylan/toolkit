//
//  PixMacAppDelegate.h
//  PixMac
//
//  Created by Santa Zhang on 8/5/10.
//  Copyright 2010 Tsinghua University. All rights reserved.
//

#import <Cocoa/Cocoa.h>

@interface PixMacAppDelegate : NSObject <NSApplicationDelegate> {
    NSWindow *window;
}

@property (assign) IBOutlet NSWindow *window;

@end
